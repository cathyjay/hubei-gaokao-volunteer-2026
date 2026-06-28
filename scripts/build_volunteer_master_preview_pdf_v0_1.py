#!/usr/bin/env python3
"""Build a PDF preview of the parent-facing volunteer master table."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
MAIN_CSV = ROOT / "data/exports/issue19-volunteer-table-v1-draft-main.csv"
MAJOR_CHOICES_CSV = ROOT / "data/exports/issue19-volunteer-table-v1-draft-major-choices.csv"
SPECIAL_CSV = ROOT / "data/exports/issue19-volunteer-table-v1-special-options.csv"
SUMMARY_JSON = ROOT / "data/exports/issue19-volunteer-table-v1-draft-summary.json"
OUTPUT_PDF = ROOT / "output/pdf/volunteer-master-table-preview-v0.1.pdf"


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


def clean_major(value: str | None) -> str:
    text = clean_text(value)
    if not text:
        return ""
    text = re.split(r"[（(]", text, maxsplit=1)[0].strip()
    text = re.split(r"(?:院校专业组|G◎|K\d{3}|C\d{3}|F\d{3}|H\d{3}|A\d{3})", text, maxsplit=1)[0].strip()
    return clean_text(text, 24)


def short_layer(value: str) -> str:
    value = clean_text(value)
    return value.split("-", 1)[0] if "-" in value else value


def signed(value: str | None) -> str:
    text = clean_text(value)
    if text == "":
        return ""
    try:
        number = int(float(text))
    except ValueError:
        return text
    return f"+{number}" if number > 0 else str(number)


def action_for_gradient(gradient: str) -> str:
    if "待补历史" in gradient:
        return "观察：先补历史映射"
    if gradient == "冲刺":
        return "少量保留，前段观察"
    if gradient == "稳冲":
        return "主线复核"
    if gradient == "稳妥":
        return "稳妥复核"
    if gradient == "保底":
        return "保底质量复核"
    return "讨论池复核"


def risk_for_row(row: dict[str, str]) -> str:
    risk = clean_text(row.get("核心风险"), 90)
    if risk:
        return risk
    layer = row.get("历史线索分层", "")
    group_size = int(row.get("专业明细行数") or 0)
    risks: list[str] = []
    if layer.startswith("H0"):
        risks.append("缺同代码历史线索")
    if group_size >= 12:
        risks.append(f"{group_size}专业大组，调剂范围需核")
    if not risks:
        risks.append("仍需核原页、官方侧、章程和完整专业组")
    return "；".join(risks)


def history_for_row(row: dict[str, str]) -> str:
    layer = short_layer(row.get("历史线索分层", ""))
    high = signed(row.get("历史最高等位分差"))
    low = signed(row.get("历史最低等位分差"))
    if high or low:
        return f"{layer}<br/>最高差{high or '-'}<br/>最低差{low or '-'}"
    return f"{layer}<br/>待补同代码历史" if layer == "H0" else layer


def fit_for_row(row: dict[str, str]) -> str:
    total = clean_text(row.get("专业明细行数")) or "?"
    preferred = clean_text(row.get("偏好专业数")) or "0"
    digital = clean_text(row.get("数字媒体技术专业数")) or "0"
    cs = clean_text(row.get("计算机类相关专业数")) or "0"
    teacher = clean_text(row.get("师范类相关专业数")) or "0"
    return f"偏好{preferred}/{total}<br/>数媒{digital} 计类{cs}<br/>师范{teacher}"


def build_major_map(rows: list[dict[str, str]]) -> dict[str, list[str]]:
    grouped: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for row in rows:
        if row.get("是否建议填入6专业") != "true":
            continue
        seq = row.get("志愿序号", "")
        try:
            order = int(row.get("专业选择顺位") or 99)
        except ValueError:
            order = 99
        name = clean_major(row.get("专业代号OCR", "") + " " + row.get("专业名称及备注短摘", ""))
        if name:
            grouped[seq].append((order, name))
    return {seq: [name for _, name in sorted(items)[:6]] for seq, items in grouped.items()}


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
    "ChineseTitle",
    parent=styles["Title"],
    fontName=FONT,
    fontSize=21,
    leading=26,
    textColor=colors.HexColor("#1f4e46"),
    alignment=TA_CENTER,
    spaceAfter=8,
)
SUBTITLE = ParagraphStyle(
    "ChineseSubtitle",
    parent=styles["Normal"],
    fontName=FONT,
    fontSize=10.5,
    leading=14,
    textColor=colors.HexColor("#44504c"),
    alignment=TA_CENTER,
    spaceAfter=8,
)
H1 = ParagraphStyle(
    "H1",
    parent=styles["Heading1"],
    fontName=FONT,
    fontSize=13,
    leading=17,
    textColor=colors.HexColor("#1f4e46"),
    spaceBefore=8,
    spaceAfter=6,
)
BODY = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName=FONT,
    fontSize=8.2,
    leading=11,
    textColor=colors.HexColor("#222222"),
    wordWrap="CJK",
)
SMALL = ParagraphStyle(
    "Small",
    parent=BODY,
    fontSize=6.2,
    leading=7.6,
    wordWrap="CJK",
)
HEADER = ParagraphStyle(
    "Header",
    parent=SMALL,
    textColor=colors.white,
    alignment=TA_CENTER,
)
CENTER = ParagraphStyle(
    "Center",
    parent=SMALL,
    alignment=TA_CENTER,
)
BADGE = ParagraphStyle(
    "Badge",
    parent=BODY,
    fontSize=9,
    leading=11,
    alignment=TA_CENTER,
    textColor=colors.white,
)


def p(text: str, style: ParagraphStyle = BODY) -> Paragraph:
    return Paragraph(clean_text(text).replace("\n", "<br/>"), style)


def row_color(gradient: str):
    if "冲刺" in gradient:
        return colors.HexColor("#fff2f0")
    if gradient == "稳冲":
        return colors.HexColor("#fff8e6")
    if gradient == "稳妥":
        return colors.HexColor("#edf7ff")
    if gradient == "保底":
        return colors.HexColor("#edf8ef")
    return colors.white


def make_badge_table(items: list[tuple[str, str, str]]) -> Table:
    data = [[p(label, BADGE), p(value, BADGE)] for label, value, _ in items]
    table = Table(data, colWidths=[31 * mm, 46 * mm], hAlign="CENTER")
    style: list[tuple] = [
        ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#d4d9d6")),
        ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#d4d9d6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for idx, (_, _, color) in enumerate(items):
        style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor(color)))
    table.setStyle(TableStyle(style))
    return table


def make_note_box(title: str, body_lines: list[str], color: str = "#f2f6f4") -> Table:
    data = [[p(f"<b>{title}</b>", BODY)], [p("<br/>".join(body_lines), BODY)]]
    table = Table(data, colWidths=[260 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(color)),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#b9c9c1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def make_main_table(main_rows: list[dict[str, str]], major_map: dict[str, list[str]]) -> LongTable:
    headers = [
        "序号",
        "梯度",
        "院校专业组",
        "城市",
        "学校/费用",
        "拟看6专业预览",
        "组内适配",
        "历史/余量",
        "调剂草案",
        "预览动作",
        "未决风险",
    ]
    data: list[list[Paragraph]] = [[p(h, HEADER) for h in headers]]
    for row in main_rows:
        seq = row.get("志愿序号", "")
        majors = "；".join(major_map.get(seq) or [])
        if not majors:
            majors = "；".join(clean_text(row.get(f"建议专业{i}"), 24) for i in range(1, 7) if row.get(f"建议专业{i}"))
        data.append(
            [
                p(seq, CENTER),
                p(row.get("草案梯度", ""), CENTER),
                p(f"{row.get('院校名称OCR', '')}<br/>{row.get('院校专业组代码OCR规范化', '')}", SMALL),
                p(clean_text(row.get("城市候选")) or "待核", CENTER),
                p(clean_text(row.get("家庭底线属性动作"), 30) or clean_text(row.get("公办民办机器线索"), 30), SMALL),
                p(clean_text(majors, 100), SMALL),
                p(fit_for_row(row), SMALL),
                p(history_for_row(row), SMALL),
                p("待定：完整组可接受后再服从", SMALL),
                p(action_for_gradient(row.get("草案梯度", "")), SMALL),
                p(risk_for_row(row), SMALL),
            ]
        )

    col_widths = [9 * mm, 15 * mm, 29 * mm, 15 * mm, 24 * mm, 57 * mm, 25 * mm, 24 * mm, 29 * mm, 23 * mm, 39 * mm]
    table = LongTable(data, colWidths=col_widths, repeatRows=1, hAlign="CENTER", splitByRow=True)
    style: list[tuple] = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e46")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#9aa6a0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.2),
        ("TOPPADDING", (0, 0), (-1, -1), 3.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
    ]
    for i, row in enumerate(main_rows, start=1):
        style.append(("BACKGROUND", (0, i), (-1, i), row_color(row.get("草案梯度", ""))))
    table.setStyle(TableStyle(style))
    return table


def make_special_table(rows: list[dict[str, str]]) -> LongTable:
    headers = ["序号", "层级", "院校专业组", "城市", "费用线索", "动作", "适配理由", "关键风险"]
    data: list[list[Paragraph]] = [[p(h, HEADER) for h in headers]]
    for row in rows:
        fee_min = clean_text(row.get("场景内最低学费"))
        fee_max = clean_text(row.get("场景内最高学费"))
        fee = fee_min if fee_min == fee_max else f"{fee_min}-{fee_max}"
        fee = f"{fee}元/年" if fee else "待核"
        data.append(
            [
                p(row.get("专项序号", ""), CENTER),
                p(row.get("专项层级", ""), SMALL),
                p(f"{row.get('院校名称OCR', '')}<br/>{row.get('院校专业组代码OCR规范化', '')}", SMALL),
                p(clean_text(row.get("城市候选")) or "待核", CENTER),
                p(fee, CENTER),
                p(row.get("家庭讨论动作", ""), SMALL),
                p(clean_text(row.get("适配理由"), 80), SMALL),
                p(clean_text(row.get("关键风险"), 80), SMALL),
            ]
        )
    col_widths = [10 * mm, 28 * mm, 42 * mm, 16 * mm, 22 * mm, 29 * mm, 72 * mm, 70 * mm]
    table = LongTable(data, colWidths=col_widths, repeatRows=1, hAlign="CENTER", splitByRow=True)
    style: list[tuple] = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#425b76")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#aab2bb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
    ]
    for i, row in enumerate(rows, start=1):
        layer = row.get("专项层级", "")
        if layer.startswith("A"):
            bg = "#eef7ff"
        elif layer.startswith("B"):
            bg = "#fff8e6"
        elif layer.startswith("E"):
            bg = "#f4f4f4"
        else:
            bg = "#ffffff"
        style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(bg)))
    table.setStyle(TableStyle(style))
    return table


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT, 7)
    canvas.setFillColor(colors.HexColor("#65706c"))
    canvas.drawString(doc.leftMargin, 10 * mm, "湖北2026本科普通批志愿总表预览 V0.1 - 非最终填报表")
    canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 10 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


def build_pdf() -> None:
    summary = read_json(SUMMARY_JSON)
    main_rows = read_csv(MAIN_CSV)
    major_rows = read_csv(MAJOR_CHOICES_CSV)
    special_rows = read_csv(SPECIAL_CSV)
    major_map = build_major_map(major_rows)
    fixed = summary["fixed_inputs"]
    eq = fixed["等位分"]

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=landscape(A4),
        leftMargin=8 * mm,
        rightMargin=8 * mm,
        topMargin=10 * mm,
        bottomMargin=15 * mm,
        title="湖北2026本科普通批志愿总表预览 V0.1",
        author="Codex",
    )

    gradient_counts = "、".join(f"{k}{v}" for k, v in summary["gradient_counts"].items())
    story = [
        Paragraph("湖北2026本科普通批志愿总表预览 V0.1", TITLE),
        Paragraph("基于现有稳定数据底座和 V1 草表生成 - 仅用于看版式和家庭讨论效果", SUBTITLE),
        Spacer(1, 4 * mm),
        make_badge_table(
            [
                ("总分", str(fixed["总分"]), "#1f4e46"),
                ("累计位次", str(fixed["累计位次"]), "#425b76"),
                ("主表", f"{summary['main_group_count']}组", "#6c5b3f"),
                ("专项", f"{summary['special_option_count']}项", "#7a4d4d"),
            ]
        ),
        Spacer(1, 5 * mm),
        make_note_box(
            "证据边界",
            [
                "本 PDF 参考机构报告的信息层级：以院校专业组为核心，同时展示专业、计划/费用线索、历史线索和风险。",
                "但本表不采用第三方概率，不是最终志愿填报表。所有主表行仍为 是否可作为定稿依据=false。",
                "正式版必须重新核第 19 期原页、湖北官方系统或省招办计划、高校章程、完整院校专业组、6 个专业顺序、计划数、学费、选科、校区、语种/单科/体检限制。",
            ],
        ),
        Spacer(1, 4 * mm),
        Table(
            [
                [p("固定输入", HEADER), p("当前内容", HEADER), p("家长阅读含义", HEADER)],
                [p("省份与批次", BODY), p(f"{fixed['省份']} {fixed['年份']} 本科普通批", BODY), p("不能照搬河南等外省志愿数量和概率口径", BODY)],
                [p("类别与选科", BODY), p(f"{fixed['类别']}；化学、地理", BODY), p("只看湖北物理类且符合选科要求的院校专业组", BODY)],
                [p("等位分参考", BODY), p(f"2025年{eq['2025']}、2024年{eq['2024']}、2023年{eq['2023']}", BODY), p("用位次和等位分判断历史线索，不只看裸分", BODY)],
                [p("家庭主线", BODY), p("公办普通低费用优先，不学医，稳第一", BODY), p("后段稳妥和保底质量比前段冲刺更重要", BODY)],
                [p("当前梯度", BODY), p(gradient_counts, BODY), p("预览版沿用 V1 草表，下一版应继续加固保底", BODY)],
            ],
            colWidths=[34 * mm, 95 * mm, 130 * mm],
            style=[
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e46")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8c2bd")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ],
        ),
        Spacer(1, 4 * mm),
        make_note_box(
            "怎么看这张表",
            [
                "先看第31-45位稳妥/保底是否能接受，再看前段冲刺。",
                "拟看6专业只是机器草排；正式填报前必须重新确定顺序，并先确认完整专业组都可接受。",
                "H0、OCR串页、专业名连读、校区/费用待核，均不能承担关键位置。",
                "高费/中外合作只放专项附录，不替代普通公办低费用主线。",
            ],
            "#fff8e6",
        ),
        PageBreak(),
        Paragraph("一、普通主线志愿总表预览", H1),
        Paragraph("说明：本表保留 OCR 待核痕迹，不手工美化疑似错字或串页内容。凡出现异常，均视为后续必须回原页和官方系统核验的风险提示。", BODY),
        Spacer(1, 2 * mm),
        make_main_table(main_rows, major_map),
        PageBreak(),
        Paragraph("二、高费/中外合作专项备选预览", H1),
        Paragraph("专项备选只作家庭单独讨论。只有费用、培养模式、证书、校区、出国要求和调剂边界全部讲清楚，才考虑进入后续版本。", BODY),
        Spacer(1, 2 * mm),
        make_special_table(special_rows),
        Spacer(1, 4 * mm),
        Paragraph("三、下一版需要补强的地方", H1),
        make_note_box(
            "从预览到正式版的升级条件",
            [
                "按最新 Round4 和稳定基座重新压缩 30-50 个家长讨论组。",
                "增加高质量保底，不只保留 5 个保底标签。",
                "逐组补齐最坏调剂结果、章程限制、校区、学费、计划数和选科。",
                "H0 和 OCR 串页风险项要么补证据，要么降级或删除。",
                "最终版建议导出正式 Excel 和 PDF：Excel 便于筛选，PDF 便于家长讨论和定稿签字。",
            ],
            "#eef7ff",
        ),
        Spacer(1, 4 * mm),
        Paragraph(f"生成日期：{date.today().isoformat()}。本文件由脚本 scripts/build_volunteer_master_preview_pdf_v0_1.py 生成。", BODY),
    ]

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"写出 PDF：{OUTPUT_PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    build_pdf()
