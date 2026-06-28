#!/usr/bin/env python3
"""Build a parent-facing volunteer master table preview from current draft data."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_CSV = ROOT / "data/exports/issue19-volunteer-table-v1-draft-main.csv"
MAJOR_CHOICES_CSV = ROOT / "data/exports/issue19-volunteer-table-v1-draft-major-choices.csv"
SPECIAL_CSV = ROOT / "data/exports/issue19-volunteer-table-v1-special-options.csv"
SUMMARY_JSON = ROOT / "data/exports/issue19-volunteer-table-v1-draft-summary.json"
OUTPUT_MD = ROOT / "docs/VOLUNTEER_MASTER_TABLE_PREVIEW_V0_1.md"


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
        return text[: limit - 1].rstrip() + "…"
    return text


def clean_major(value: str | None) -> str:
    text = clean_text(value)
    if not text:
        return ""
    text = re.split(r"[（(]", text, maxsplit=1)[0].strip()
    text = re.split(r"(?:院校专业组|G◎|K\d{3}|C\d{3}|F\d{3}|H\d{3})", text, maxsplit=1)[0].strip()
    return clean_text(text, 24)


def md_escape(value: str | None) -> str:
    return clean_text(value).replace("\\", "\\\\").replace("`", "\\`")


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
    risk = clean_text(row.get("核心风险"), 92)
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
        return f"{layer}；最高差{high or '-'}，最低差{low or '-'}"
    return f"{layer}；待补同代码历史" if layer == "H0" else layer


def fit_for_row(row: dict[str, str]) -> str:
    total = clean_text(row.get("专业明细行数")) or "?"
    preferred = clean_text(row.get("偏好专业数")) or "0"
    digital = clean_text(row.get("数字媒体技术专业数")) or "0"
    cs = clean_text(row.get("计算机类相关专业数")) or "0"
    teacher = clean_text(row.get("师范类相关专业数")) or "0"
    return f"偏好{preferred}/{total}；数媒{digital}、计类{cs}、师范{teacher}"


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
    result: dict[str, list[str]] = {}
    for seq, items in grouped.items():
        result[seq] = [name for _, name in sorted(items)[:6]]
    return result


def main_table_rows(main_rows: list[dict[str, str]], major_map: dict[str, list[str]]) -> list[str]:
    lines = [
        "| 序号 | 梯度 | 院校专业组 | 城市/校区 | 学校与费用线索 | 拟看 6 专业预览 | 组内适配 | 历史/余量 | 调剂草案 | 预览动作 | 未决风险 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in main_rows:
        seq = row.get("志愿序号", "")
        school_group = f"{row.get('院校名称OCR', '')} {row.get('院校专业组代码OCR规范化', '')}"
        city = clean_text(row.get("城市候选")) or "待核"
        school_attr = clean_text(row.get("家庭底线属性动作"), 28) or clean_text(row.get("公办民办机器线索"), 28)
        majors = "；".join(major_map.get(seq) or [clean_text(row.get(f"建议专业{i}"), 24) for i in range(1, 7) if row.get(f"建议专业{i}")])
        majors = clean_text(majors, 96) or "待核"
        transfer = "待定：完整专业组可接受后再服从"
        line = [
            seq,
            row.get("草案梯度", ""),
            school_group,
            city,
            school_attr,
            majors,
            fit_for_row(row),
            history_for_row(row),
            transfer,
            action_for_gradient(row.get("草案梯度", "")),
            risk_for_row(row),
        ]
        lines.append("| " + " | ".join(md_escape(item) for item in line) + " |")
    return lines


def special_table_rows(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| 专项序号 | 层级 | 院校专业组 | 城市 | 费用线索 | 家庭讨论动作 | 适配理由 | 关键风险 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        fee_min = clean_text(row.get("场景内最低学费"))
        fee_max = clean_text(row.get("场景内最高学费"))
        fee = fee_min if fee_min == fee_max else f"{fee_min}-{fee_max}"
        if fee:
            fee += " 元/年"
        else:
            fee = "待核"
        line = [
            row.get("专项序号", ""),
            row.get("专项层级", ""),
            f"{row.get('院校名称OCR', '')} {row.get('院校专业组代码OCR规范化', '')}",
            clean_text(row.get("城市候选")) or "待核",
            fee,
            row.get("家庭讨论动作", ""),
            clean_text(row.get("适配理由"), 70),
            clean_text(row.get("关键风险"), 70),
        ]
        lines.append("| " + " | ".join(md_escape(item) for item in line) + " |")
    return lines


def main() -> None:
    summary = read_json(SUMMARY_JSON)
    main_rows = read_csv(MAIN_CSV)
    major_rows = read_csv(MAJOR_CHOICES_CSV)
    special_rows = read_csv(SPECIAL_CSV)
    major_map = build_major_map(major_rows)

    fixed = summary["fixed_inputs"]
    eq = fixed["等位分"]
    gradient_counts = "、".join(f"{k}{v}" for k, v in summary["gradient_counts"].items())

    lines: list[str] = [
        "# 本科普通批志愿总表预览 V0.1",
        "",
        "生成日期：2026-06-28",
        "",
        "报告状态：预览版，只用于看总表结构和家庭讨论效果，不是最终志愿填报表。",
        "",
        "证据边界：本表来自现有 `issue19-volunteer-table-v1-draft` 草表和逐专业选择草案；所有主表行仍为 `是否可作为定稿依据=false`。正式版必须重新核第 19 期原页、湖北官方系统或省招办计划、高校招生章程、完整院校专业组、6 个专业顺序、计划数、学费、选科、校区、语种/单科/体检限制。",
        "",
        "## 一、固定输入",
        "",
        f"- 省份与批次：{fixed['省份']} {fixed['年份']} 本科普通批。",
        f"- 类别与选科：{fixed['类别']}。",
        f"- 成绩基线：总分 {fixed['总分']}，累计位次 {fixed['累计位次']}。",
        f"- 等位分参考：2025 年 {eq['2025']}、2024 年 {eq['2024']}、2023 年 {eq['2023']}。",
        f"- 家庭主线：{fixed['主线']}；稳第一，公办普通低费用优先，专业组完整调剂范围必须可接受。",
        "",
        "## 二、预览版结构",
        "",
        f"- 主表数量：{summary['main_group_count']} 个院校专业组。",
        f"- 专业选择草案：{summary['major_choice_row_count']} 条逐专业明细。",
        f"- 专项备选：{summary['special_option_count']} 个高费/中外合作等专项项，单独放在附录，不混入普通低费用主线。",
        f"- 当前梯度：{gradient_counts}。",
        "- 重要提醒：当前排序沿用 V1 草表，不代表最终排序。下一版应按最新家庭口径继续减少缺证据高冲、提高稳妥和高质量保底。",
        "",
        "## 三、志愿总表预览",
        "",
        "表中“拟看 6 专业预览”是机器草排，目的只是让家里先看专业方向是否大体能接受。正式填报前必须重新确定 6 个专业顺序，并且先看完整专业组是否都能接受调剂。",
        "",
        "说明：本预览保留部分 OCR 待核痕迹，不手工美化专业名称。凡出现疑似错字、串页、串校、专业名连读的地方，都应视为后续必须核原页和官方系统的风险提示。",
        "",
        *main_table_rows(main_rows, major_map),
        "",
        "## 四、专项备选预览",
        "",
        "以下高费/中外合作等项目只作专项讨论，不进入普通主表。只有家庭明确接受费用、培养模式、证书、校区、出国要求和调剂边界后，才考虑是否进入后续版本。",
        "",
        *special_table_rows(special_rows),
        "",
        "## 五、这张预览表怎么看",
        "",
        "1. 先看后 15 个稳妥和保底是否家里能接受；如果后段质量不够，前面的冲刺再漂亮也不安全。",
        "2. 再看每个专业组的“组内适配”：偏好专业多不等于可填，关键是完整专业组里有没有不能接受的专业。",
        "3. `H0`、冲刺待补历史、OCR 串页或组边界风险项，不能承担关键位置，只能先补证据。",
        "4. “待定服从调剂”不是犹豫，而是正确状态：只有完整组内专业都可接受，才建议服从调剂以降低退档风险。",
        "5. 专项备选必须单独讨论，不用它们替代普通公办低费用主线。",
        "",
        "## 六、下一版要补强的地方",
        "",
        "- 按最新 Round4 和稳定基座重新压缩 30-50 个家长讨论组。",
        "- 增加高质量保底，不只保留 5 个保底标签。",
        "- 对每个保留组补齐最坏调剂结果、章程限制、校区和学费确认。",
        "- 把 H0 和 OCR 串页风险项降级或补证据后再决定是否保留。",
        "- 最终版再导出正式 Excel，并按冲稳保、普通主线、专项附录分 sheet 展示。",
        "",
    ]

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"写出志愿总表预览：{OUTPUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
