#!/usr/bin/env python3
"""Build the expanded parent discussion PDF for school/group selection."""

from __future__ import annotations

import csv
import html
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
BASELINE_JSON = ROOT / "candidate-baseline.json"
MAIN_GROUPS_CSV = ROOT / "data/exports/issue19-round4-city-gradient-candidate-groups.csv"
PRIORITY_GROUPS_CSV = ROOT / "data/exports/issue19-round4-city-gradient-priority120-groups.csv"
HISTORY_MISSING_CSV = ROOT / "data/exports/issue19-round4-city-gradient-history-missing-groups.csv"
MAJOR_DETAILS_CSV = ROOT / "data/exports/issue19-round4-city-gradient-major-details.csv"
SPECIAL_OPTIONS_CSV = ROOT / "data/exports/issue19-volunteer-table-v1-special-options.csv"
ROUND4_SUMMARY_JSON = ROOT / "data/exports/issue19-round4-city-gradient-summary.json"
SECTION_JSON = ROOT / "data/derived/hubei-2026-physics-section-static-gaokao-cn.json"
OUTPUT_PDF = ROOT / "output/pdf/volunteer-discussion-school-list-preview-v0.2.pdf"

YEARS = ("2025", "2024", "2023")
YEAR_SHORT = {"2025": "25", "2024": "24", "2023": "23"}
GRADIENT_ORDER = {
    "保底观察": 0,
    "稳妥观察": 1,
    "稳冲观察": 2,
    "冲刺观察": 3,
    "历史待补": 4,
    "高冲暂缓": 5,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_text(value: str | None, limit: int | None = None) -> str:
    text = (value or "").replace("\r", " ").replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("|", "／")
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def escape_line(value: str | None, limit: int | None = None) -> str:
    return html.escape(clean_text(value, limit), quote=False)


def para(text: str | None, style: ParagraphStyle, limit: int | None = None) -> Paragraph:
    return Paragraph(escape_line(text, limit).replace("\n", "<br/>"), style)


def rich(lines: Iterable[str], style: ParagraphStyle) -> Paragraph:
    return Paragraph("<br/>".join(lines), style)


def to_int(value: str | None, default: int = 0) -> int:
    text = clean_text(value)
    if text == "":
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def short_layer(value: str | None) -> str:
    text = clean_text(value)
    return text.split("-", 1)[0] if "-" in text else text


def extract_signed_delta(value: str | None) -> str:
    text = clean_text(value)
    if not text:
        return ""
    match = re.search(r"=([+-]?\d+)", text)
    if match:
        number = int(match.group(1))
        return f"+{number}" if number > 0 else str(number)
    match = re.search(r"([+-]?\d+)$", text)
    if match:
        number = int(match.group(1))
        return f"+{number}" if number > 0 else str(number)
    return text


def parse_score_range(value: str | None) -> tuple[int, int] | None:
    text = clean_text(value)
    match = re.fullmatch(r"(\d+)(?:-(\d+))?", text)
    if not match:
        return None
    first = int(match.group(1))
    second = int(match.group(2) or first)
    return min(first, second), max(first, second)


def register_fonts() -> str:
    font_name = "ArialUnicode"
    candidates = [
        Path("/Library/Fonts/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont(font_name, str(candidate), validate=0))
            return font_name
    raise RuntimeError("Missing Arial Unicode.ttf; cannot build a portable Chinese PDF.")


FONT = register_fonts()
styles = getSampleStyleSheet()
TITLE = ParagraphStyle(
    "TitleCN",
    parent=styles["Title"],
    fontName=FONT,
    fontSize=20,
    leading=25,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#1f4e46"),
    spaceAfter=7,
)
SUBTITLE = ParagraphStyle(
    "SubtitleCN",
    parent=styles["Normal"],
    fontName=FONT,
    fontSize=9.8,
    leading=13,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#46534f"),
)
H1 = ParagraphStyle(
    "HeadingCN",
    parent=styles["Heading1"],
    fontName=FONT,
    fontSize=12.5,
    leading=16,
    textColor=colors.HexColor("#1f4e46"),
    spaceBefore=6,
    spaceAfter=5,
)
BODY = ParagraphStyle(
    "BodyCN",
    parent=styles["Normal"],
    fontName=FONT,
    fontSize=8.2,
    leading=10.5,
    wordWrap="CJK",
    textColor=colors.HexColor("#222222"),
)
SMALL = ParagraphStyle(
    "SmallCN",
    parent=BODY,
    fontSize=5.65,
    leading=6.85,
    wordWrap="CJK",
)
TINY = ParagraphStyle(
    "TinyCN",
    parent=BODY,
    fontSize=5.15,
    leading=6.25,
    wordWrap="CJK",
)
HEADER = ParagraphStyle(
    "HeaderCN",
    parent=SMALL,
    alignment=TA_CENTER,
    textColor=colors.white,
)
CENTER = ParagraphStyle(
    "CenterCN",
    parent=SMALL,
    alignment=TA_CENTER,
)
BADGE = ParagraphStyle(
    "BadgeCN",
    parent=BODY,
    fontSize=8.8,
    leading=10.8,
    alignment=TA_CENTER,
    textColor=colors.white,
)


def load_rank_lookup() -> dict[str, list[tuple[int, int, str]]]:
    section = read_json(SECTION_JSON)
    search = section["data"]["search"]
    rank_lookup: dict[str, dict[tuple[int, int], str]] = {year: {} for year in YEARS}
    for item in search.values():
        for appositive in item.get("appositive_fraction", []):
            year = str(appositive.get("year"))
            if year not in rank_lookup:
                continue
            score_range = parse_score_range(appositive.get("score"))
            if not score_range:
                continue
            rank_lookup[year].setdefault(score_range, clean_text(appositive.get("rank_range")))
    flattened: dict[str, list[tuple[int, int, str]]] = {}
    for year, ranges in rank_lookup.items():
        flattened[year] = sorted(
            [(low, high, rank_range) for (low, high), rank_range in ranges.items()],
            key=lambda item: (item[1] - item[0], item[0]),
        )
    return flattened


def rank_for_score(rank_lookup: dict[str, list[tuple[int, int, str]]], year: str, score: str | None) -> str:
    number = to_int(score, default=-1)
    if number < 0:
        return ""
    for low, high, rank_range in rank_lookup.get(year, []):
        if low <= number <= high:
            return rank_range
    return ""


def normalize_key(row: dict[str, str]) -> str:
    return clean_text(
        row.get("院校专业组代码")
        or row.get("院校专业组代码OCR规范化")
        or row.get("2026院校专业组代码")
    )


def dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for row in rows:
        key = normalize_key(row) or clean_text(row.get("专业组出现ID"))
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def sort_group_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    def key(row: dict[str, str]) -> tuple[int, int, float, str]:
        gradient = clean_text(row.get("冲稳保"))
        priority = 0 if row.get("是否进入优先讨论") == "true" else 1
        try:
            score = -float(row.get("讨论排序分") or 0)
        except ValueError:
            score = 0
        return (priority, GRADIENT_ORDER.get(gradient, 9), score, normalize_key(row))

    return sorted(rows, key=key)


def major_weight(row: dict[str, str]) -> tuple[int, int, str]:
    text = " ".join(
        clean_text(row.get(field))
        for field in ["专业名称及备注", "专业偏好方向", "第四轮方向标签", "专业角色判断", "机器专业接受度初判"]
    )
    risk = clean_text(row.get("专业风险类型"))
    if "默认不能接受" in text or "医学" in risk or "护理" in risk or "高收费" in risk:
        penalty = 20
    elif "特殊限制" in risk or "语种" in risk or "体检" in risk:
        penalty = 6
    else:
        penalty = 0

    if "数字媒体" in text:
        base = 0
    elif any(token in text for token in ["计算机", "软件", "人工智能", "数据科学", "大数据", "网络空间", "信息安全", "物联网"]):
        base = 1
    elif any(token in text for token in ["电子", "通信", "网络"]):
        base = 2
    elif "师范" in text:
        base = 3
    elif any(token in text for token in ["自动化", "机器", "电气", "智能制造"]):
        base = 4
    else:
        base = 9
    return base + penalty, to_int(row.get("专业组内专业序号"), 99), clean_text(row.get("专业名称及备注"))


def clean_major_name(row: dict[str, str]) -> str:
    code = clean_text(row.get("专业代号"))
    name = clean_text(row.get("专业名称及备注"))
    name = re.sub(r"\[M-[0-9a-f]+\]", "", name)
    name = re.sub(r"（办学地点[^）]*）", "", name)
    name = re.sub(r"（[^）]{18,}）", "", name)
    name = re.split(r"(?:[A-Z]\d{3}\s|院校专业组及专业代号|G◎)", name, maxsplit=1)[0]
    name = clean_text(name, 24)
    plan = clean_text(row.get("专业计划数OCR候选"))
    fee = clean_text(row.get("学费OCR候选"))
    suffix_parts = []
    if plan and plan.isdigit():
        suffix_parts.append(f"计{plan}")
    if fee and fee.isdigit():
        suffix_parts.append(f"费{fee}")
    suffix = f"({'/'.join(suffix_parts)})" if suffix_parts else ""
    return clean_text(f"{code} {name}{suffix}", 34)


def build_major_map(rows: list[dict[str, str]]) -> dict[str, list[str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = normalize_key(row)
        if key:
            grouped[key].append(row)

    result: dict[str, list[str]] = {}
    for key, items in grouped.items():
        chosen: list[str] = []
        for row in sorted(items, key=major_weight):
            name = clean_major_name(row)
            if name and name not in chosen:
                chosen.append(name)
            if len(chosen) >= 6:
                break
        result[key] = chosen
    return result


def gradient_color(gradient: str) -> str:
    if gradient == "保底观察":
        return "#edf8ef"
    if gradient == "稳妥观察":
        return "#edf7ff"
    if gradient == "稳冲观察":
        return "#fff8e6"
    if gradient == "冲刺观察":
        return "#fff2f0"
    if gradient == "历史待补":
        return "#f5f0ff"
    return "#ffffff"


def compact_attribute(row: dict[str, str]) -> str:
    city = clean_text(row.get("城市") or row.get("城市候选") or row.get("教育部所在地")) or "城市待核"
    province = clean_text(row.get("省份"))
    attr = "公办/普通费线索" if "非民办" in clean_text(row.get("公办民办机器线索")) else clean_text(row.get("学校登记备注") or row.get("公办民办机器线索"), 14)
    location_note = "校区待核" if "pending" in clean_text(row.get("校区字段状态")) else ""
    lines = [escape_line(city if not province or province in city else f"{city} / {province}", 24)]
    lines.append(escape_line(attr, 24))
    if location_note:
        lines.append(escape_line(location_note, 12))
    return "<br/>".join(lines)


def major_summary(row: dict[str, str], major_map: dict[str, list[str]]) -> str:
    key = normalize_key(row)
    majors = major_map.get(key, [])
    counts = []
    mapping = [
        ("数媒", "数字媒体技术专业数"),
        ("计/AI/软", "计算机AI软件专业数"),
        ("计类", "计算机类相关专业数"),
        ("电子网", "电子信息网络专业数"),
        ("师范", "师范类相关专业数"),
        ("机械自", "机械自动化机器人专业数"),
    ]
    for label, field in mapping:
        count = to_int(row.get(field))
        if count:
            counts.append(f"{label}{count}")
    total = clean_text(row.get("专业明细行数")) or "?"
    line1 = f"命中 {' '.join(counts) if counts else '待了解'} / 共{total}"
    line2 = "看 " + "；".join(majors[:4]) if majors else clean_text(row.get("组内专业摘录"), 58)
    return "<br/>".join([escape_line(line1, 44), escape_line(line2, 86)])


def history_detail(
    row: dict[str, str],
    rank_lookup: dict[str, list[tuple[int, int, str]]],
) -> str:
    layer = short_layer(row.get("历史线索分层"))
    if layer == "H0" or clean_text(row.get("冲稳保")) == "历史待补":
        return "<br/>".join(
            [
                escape_line("H0 无同代码历史"),
                escape_line("先补同校同类组/官方投档线"),
                escape_line("未补前不承担稳保位置"),
            ]
        )

    lines = [escape_line(f"{layer} {clean_text(row.get('冲稳保'))}", 30)]
    for year in YEARS:
        score = clean_text(row.get(f"{year}投档分"))
        if not score:
            lines.append(escape_line(f"{YEAR_SHORT[year]} 无同代码"))
            continue
        delta = extract_signed_delta(row.get(f"{year}等位分差"))
        rank = rank_for_score(rank_lookup, year, score)
        rank_text = f" 位{rank}" if rank else " 位次待补"
        lines.append(escape_line(f"{YEAR_SHORT[year]} 投{score}({delta}){rank_text}", 45))
    return "<br/>".join(lines)


def transfer_plan(row: dict[str, str]) -> str:
    total = max(to_int(row.get("专业明细行数")), 1)
    preferred = to_int(row.get("数字媒体技术专业数")) + to_int(row.get("计算机AI软件专业数")) + to_int(row.get("师范类相关专业数"))
    special = to_int(row.get("特殊限制待核专业数"))
    excluded = (
        to_int(row.get("护理助产专业数"))
        + to_int(row.get("动物医学兽医专业数"))
        + to_int(row.get("临床口腔中医暂缓专业数"))
        + to_int(row.get("医技护理康复专业数"))
    )
    transfer = clean_text(row.get("调剂初判"))

    if "结构异常" in transfer:
        return "先不谈服从；核完整组是否串页/漏行。"
    if "默认不能接受" in transfer or excluded:
        return "默认不服从；除非确认不可接受项不在同组。"
    if "特殊限制" in transfer or special:
        return "先核语种/单科/体检；未闭环不放稳段。"
    if "学费字段" in transfer:
        return "先核学费；超预算则删或转专项。"
    if preferred / total >= 0.45 and total <= 14:
        return "可进服从讨论；完整组可接受率达70%再服从。"
    if total >= 18:
        return "大组谨慎；圈出最差调剂3项，能接受才服从。"
    return "偏好不算多；先确认非偏好专业底线。"


def tomorrow_action(row: dict[str, str], index_label: str) -> str:
    gradient = clean_text(row.get("冲稳保"))
    priority = row.get("是否进入优先讨论") == "true"
    page = clean_text(row.get("来源页码"))
    side = clean_text(row.get("版面列"))
    verify = f"核P{page}{side[:1]}" if page else "核原页"
    prefix = "优先勾选" if priority else "二轮备选"

    if gradient == "保底观察":
        action = "先确认能读4年；不接受就删，保底不留遗憾项。"
    elif gradient == "稳妥观察":
        action = "重点比较同梯度；确认专业组和调剂底线。"
    elif gradient == "稳冲观察":
        action = "看是否比稳妥组更值得；好专业集中才保留。"
    elif gradient == "冲刺观察":
        action = "只占前段少量名额；学校/城市特别认可才留。"
    else:
        action = "先补历史证据；补齐前只做观察。"
    return f"{index_label} {prefix}；{action} {verify}。"


def risk_summary(row: dict[str, str]) -> str:
    risks = []
    review = clean_text(row.get("保真核验层级"))
    if review:
        risks.append(review.split("-", 1)[0])
    for field, label in [
        ("特殊限制待核专业数", "限"),
        ("字段缺口专业行数", "缺"),
        ("高收费或超预算专业数", "费"),
        ("护理助产专业数", "护"),
        ("动物医学兽医专业数", "兽"),
    ]:
        count = to_int(row.get(field))
        if count:
            risks.append(f"{label}{count}")
    page = clean_text(row.get("来源页码"))
    side = clean_text(row.get("版面列"))
    if page:
        risks.append(f"P{page}{side[:1]}")
    if not risks:
        risks.append("仍需原页/官方/章程")
    return "；".join(risks[:6])


def make_badge_table(items: list[tuple[str, str, str]]) -> Table:
    data = [[para(label, BADGE), para(value, BADGE)] for label, value, _ in items]
    table = Table(data, colWidths=[31 * mm, 42 * mm], hAlign="CENTER")
    style: list[tuple] = [
        ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#d4d9d6")),
        ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#d4d9d6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for index, (_, _, color) in enumerate(items):
        style.append(("BACKGROUND", (0, index), (-1, index), colors.HexColor(color)))
    table.setStyle(TableStyle(style))
    return table


def make_note_box(title: str, body_lines: list[str], color: str = "#f2f6f4") -> Table:
    data = [
        [rich([f"<b>{escape_line(title)}</b>"], BODY)],
        [rich([escape_line(line) for line in body_lines], BODY)],
    ]
    table = Table(data, colWidths=[272 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(color)),
                ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor("#b9c9c1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def make_equivalent_table(baseline: dict) -> Table:
    eq = baseline["equivalent_scores"]
    rows = [[para("年份", HEADER), para("我方等位分", HEADER), para("我方等位位次段", HEADER), para("用途", HEADER)]]
    for year in YEARS:
        item = eq[year]
        rows.append(
            [
                para(year, CENTER),
                para(str(item["score"]), CENTER),
                para(item["rank_range"], CENTER),
                para("本 PDF 的历史余量均按投档分减该年等位分计算", SMALL),
            ]
        )
    table = Table(rows, colWidths=[28 * mm, 35 * mm, 60 * mm, 149 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e46")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b8c2bd")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def make_group_table(
    rows: list[dict[str, str]],
    major_map: dict[str, list[str]],
    rank_lookup: dict[str, list[tuple[int, int, str]]],
    prefix: str,
) -> LongTable:
    headers = ["编号", "梯度", "院校专业组", "城市/属性", "专业线索", "历史分位/排位", "调剂讨论", "明日动作", "风险/页码"]
    data: list[list[Paragraph]] = [[para(header, HEADER) for header in headers]]
    for index, row in enumerate(rows, start=1):
        label = f"{prefix}{index:03d}"
        group_name = f"{clean_text(row.get('院校名称') or row.get('院校名称OCR'))}<br/>{clean_text(row.get('院校专业组代码') or row.get('院校专业组代码OCR规范化'))}"
        data.append(
            [
                para(label, CENTER),
                para(clean_text(row.get("冲稳保")), CENTER),
                Paragraph(group_name, SMALL),
                rich([compact_attribute(row)], SMALL),
                rich([major_summary(row, major_map)], TINY),
                rich([history_detail(row, rank_lookup)], TINY),
                para(transfer_plan(row), SMALL),
                para(tomorrow_action(row, label), TINY),
                para(risk_summary(row), TINY),
            ]
        )

    col_widths = [12 * mm, 17 * mm, 30 * mm, 24 * mm, 54 * mm, 45 * mm, 35 * mm, 38 * mm, 29 * mm]
    table = LongTable(data, colWidths=col_widths, repeatRows=1, hAlign="CENTER", splitByRow=True)
    style: list[tuple] = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e46")),
        ("GRID", (0, 0), (-1, -1), 0.24, colors.HexColor("#9aa6a0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.0),
        ("TOPPADDING", (0, 0), (-1, -1), 2.7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.7),
    ]
    for index, row in enumerate(rows, start=1):
        style.append(("BACKGROUND", (0, index), (-1, index), colors.HexColor(gradient_color(clean_text(row.get("冲稳保"))))))
    table.setStyle(TableStyle(style))
    return table


def make_special_table(rows: list[dict[str, str]]) -> LongTable:
    headers = ["编号", "层级", "院校专业组", "城市", "费用", "为什么看", "必须问清", "讨论动作"]
    data: list[list[Paragraph]] = [[para(header, HEADER) for header in headers]]
    for index, row in enumerate(rows, start=1):
        fee_min = clean_text(row.get("场景内最低学费"))
        fee_max = clean_text(row.get("场景内最高学费"))
        fee = fee_min if fee_min == fee_max else f"{fee_min}-{fee_max}"
        if fee:
            fee = f"{fee}元/年"
        data.append(
            [
                para(f"S{index:03d}", CENTER),
                para(row.get("专项层级"), SMALL),
                rich(
                    [
                        escape_line(row.get("院校名称OCR")),
                        escape_line(row.get("院校专业组代码OCR规范化")),
                    ],
                    SMALL,
                ),
                para(clean_text(row.get("城市候选")) or "待核", CENTER),
                para(fee or "待核", CENTER),
                para(row.get("适配理由"), SMALL, 74),
                para(row.get("关键风险"), SMALL, 78),
                para("费用/证书/培养模式/语种单科/调剂边界逐项确认；不确认不进主表。", SMALL),
            ]
        )
    table = LongTable(
        data,
        colWidths=[13 * mm, 28 * mm, 36 * mm, 17 * mm, 23 * mm, 68 * mm, 68 * mm, 31 * mm],
        repeatRows=1,
        hAlign="CENTER",
        splitByRow=True,
    )
    style: list[tuple] = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#425b76")),
        ("GRID", (0, 0), (-1, -1), 0.24, colors.HexColor("#aab2bb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.8),
    ]
    for index, row in enumerate(rows, start=1):
        layer = clean_text(row.get("专项层级"))
        bg = "#eef7ff" if layer.startswith("A") else "#fff8e6" if layer.startswith("B") else "#f4f4f4"
        style.append(("BACKGROUND", (0, index), (-1, index), colors.HexColor(bg)))
    table.setStyle(TableStyle(style))
    return table


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT, 7)
    canvas.setFillColor(colors.HexColor("#65706c"))
    canvas.drawString(doc.leftMargin, 10 * mm, "湖北2026本科普通批学校/专业组初筛讨论版 V0.2 - 非最终填报表")
    canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 10 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


def build_pdf() -> None:
    baseline = read_json(BASELINE_JSON)
    summary = read_json(ROUND4_SUMMARY_JSON)
    priority_keys = {normalize_key(row) for row in read_csv(PRIORITY_GROUPS_CSV)}
    main_rows = dedupe_rows(read_csv(MAIN_GROUPS_CSV))
    for row in main_rows:
        row["是否进入优先讨论"] = "true" if normalize_key(row) in priority_keys else clean_text(row.get("是否进入优先讨论"))
    priority_rows = sort_group_rows([row for row in main_rows if row.get("是否进入优先讨论") == "true"])
    extended_rows = sort_group_rows([row for row in main_rows if row.get("是否进入优先讨论") != "true"])
    history_missing_rows = sort_group_rows(dedupe_rows(read_csv(HISTORY_MISSING_CSV)))
    major_map = build_major_map(read_csv(MAJOR_DETAILS_CSV))
    rank_lookup = load_rank_lookup()
    special_rows = read_csv(SPECIAL_OPTIONS_CSV)

    candidate = baseline["rank_2026"]
    scores = baseline["scores"]
    gradient_counts = Counter(row.get("冲稳保") for row in main_rows)
    gradient_text = "、".join(f"{key}{gradient_counts[key]}" for key in ["保底观察", "稳妥观察", "稳冲观察", "冲刺观察"] if gradient_counts.get(key))

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=landscape(A4),
        leftMargin=6 * mm,
        rightMargin=6 * mm,
        topMargin=8 * mm,
        bottomMargin=14 * mm,
        title="湖北2026本科普通批学校专业组初筛讨论版 V0.2",
        author="Codex",
    )

    story = [
        Paragraph("湖北2026本科普通批学校/专业组初筛讨论版 V0.2", TITLE),
        Paragraph("基于当前个人基础信息和现有数据底座生成 - 用于明日打印、勾选、讨论，不作最终填报依据", SUBTITLE),
        Spacer(1, 3 * mm),
        make_badge_table(
            [
                ("总分", str(scores["总分"]), "#1f4e46"),
                ("位次", str(candidate["cumulative_rank"]), "#425b76"),
                ("主线全集", f"{len(main_rows)}组", "#6c5b3f"),
                ("优先讨论", f"{len(priority_rows)}组", "#7a4d4d"),
                ("历史待补", f"{len(history_missing_rows)}组", "#6a5a86"),
                ("专项附录", f"{len(special_rows)}项", "#5d6e49"),
            ]
        ),
        Spacer(1, 4 * mm),
        make_note_box(
            "本版怎么用",
            [
                "这版不是最终志愿顺序，而是初筛讨论清单：先圈学校/城市/专业组是否愿意继续核，再谈最终45个志愿怎么排。",
                "主线全集328组来自Round4：公办普通学费机器线索、剔除医学护理兽医等明确不进主线方向、且按同代码历史线属于可讨论范围。",
                "历史待补208组也可能有合适专业，但缺同代码投档线，不和主线全集混排；明天只决定是否值得补证据。",
                "每一行的历史列展示历史投档分、与我方等位分差、该年投档位次段；括号内+/-为投档分减当年等位分。",
            ],
            "#f2f6f4",
        ),
        Spacer(1, 3 * mm),
        Table(
            [
                [para("固定输入", HEADER), para("当前内容", HEADER), para("讨论含义", HEADER)],
                [
                    para("考生基础", BODY),
                    para(f"湖北 2026 普通类首选物理；再选化学/地理；总分{scores['总分']}；位次段{candidate['rank_range']}", BODY),
                    para("只讨论湖北本科普通批院校专业组，不照搬外省报告口径。", BODY),
                ],
                [
                    para("家庭主线", BODY),
                    para("优先公办、普通学费、稳第一；当前偏好含计算机/数字媒体/师范等可解释方向。", BODY),
                    para("先保证后段能接受，再把前段冲刺做得有价值。", BODY),
                ],
                [
                    para("主线分布", BODY),
                    para(gradient_text, BODY),
                    para("当前保底机器标签偏少，所以后续仍要继续补高质量保底。", BODY),
                ],
                [
                    para("证据边界", BODY),
                    para(summary["source_policy"], BODY),
                    para("所有行仍需第19期原页、湖北官方系统/省招办计划、高校章程、学费校区和完整调剂范围复核。", BODY),
                ],
            ],
            colWidths=[34 * mm, 118 * mm, 120 * mm],
            style=[
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e46")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b8c2bd")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ],
        ),
        Spacer(1, 3 * mm),
        make_equivalent_table(baseline),
        Spacer(1, 3 * mm),
        make_note_box(
            "明天讨论建议顺序",
            [
                "1. 先看A表优先讨论120组：逐行打勾 保留/删除/待核，不要急着排序。",
                "2. 再看B表扩展208组：只挑特别愿意继续核的学校或专业组。",
                "3. C表历史待补只决定是否补证据；D表高费/中外合作只做单独预算和培养模式讨论。",
                "4. 任一组如果完整专业组最差调剂结果不能接受，就不能放在稳妥或保底位置。",
            ],
            "#fff8e6",
        ),
        PageBreak(),
        Paragraph("A. 优先讨论120组", H1),
        Paragraph("排序按讨论用途处理：先看保底/稳妥，再看稳冲/冲刺。该顺序不是最终志愿填报顺序。", BODY),
        Spacer(1, 2 * mm),
        make_group_table(priority_rows, major_map, rank_lookup, "A"),
        PageBreak(),
        Paragraph("B. 主线可讨论全集 - 其余208组", H1),
        Paragraph("这些仍符合主线机器硬条件，但不如A表优先。明天建议只圈出特别想继续看的学校/城市/专业方向。", BODY),
        Spacer(1, 2 * mm),
        make_group_table(extended_rows, major_map, rank_lookup, "B"),
        PageBreak(),
        Paragraph("C. 历史待补索引208组", H1),
        Paragraph("这部分缺同代码历史线索，不能直接判断冲稳保。只用于决定是否值得继续补证据，不用于最终排序。", BODY),
        Spacer(1, 2 * mm),
        make_group_table(history_missing_rows, major_map, rank_lookup, "H"),
        PageBreak(),
        Paragraph("D. 高费/中外合作专项附录", H1),
        Paragraph("专项项不替代普通公办低费用主线。只有费用、证书、培养模式、语种/单科、校区和调剂边界都讲清楚，才考虑进入下一版。", BODY),
        Spacer(1, 2 * mm),
        make_special_table(special_rows),
        Spacer(1, 4 * mm),
        make_note_box(
            "从讨论版到下一版",
            [
                "把A/B/H/S表逐行标注：保留、删除、待核、转专项。",
                "对保留项补齐官方计划、原页截图位置、章程限制、完整专业组、学费、校区、计划数和调剂底线。",
                "把家长确认后的保留项压缩为45个院校专业组，并重新生成正式志愿总表和Excel筛选版。",
            ],
            "#eef7ff",
        ),
        Spacer(1, 3 * mm),
        Paragraph(f"生成日期：{date.today().isoformat()}。生成脚本：scripts/build_volunteer_discussion_pdf_v0_2.py。", BODY),
    ]

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"写出 PDF：{OUTPUT_PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    build_pdf()
