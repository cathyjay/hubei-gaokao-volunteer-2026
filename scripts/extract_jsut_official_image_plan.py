#!/usr/bin/env python3
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_IMAGE = ROOT / "data/external/issue19-b0-b1-official-sources/jsut-2026-hubei-plan.jpg"
SOURCE_ENTRY = ROOT / "data/external/issue19-b0-b1-official-sources/jsut-zs-home-2026-plan-links.html"
OUTPUT_CSV = ROOT / "data/external/issue19-b0-b1-official-sources/jsut-2026-hubei-physics-plan-extracted.csv"

FIELDS = [
    "学校名称",
    "原始图片",
    "官网入口页",
    "类别",
    "专业名称",
    "科类",
    "学制",
    "学费",
    "湖北计划数",
    "提取方法",
    "提取局限性",
]

ROWS = [
    ("会计学", "1", "四年", "5200"),
    ("应用心理学", "1", "四年", "5500"),
    ("电气工程及其自动化", "2", "四年", "5800"),
    ("通信工程", "1", "四年", "5800"),
    ("自动化", "1", "四年", "5800"),
    ("功能材料", "2", "四年", "5800"),
    ("储能科学与工程", "1", "四年", "5800"),
    ("机械电子工程", "1", "四年", "5800"),
    ("过程装备与控制工程", "1", "四年", "5800"),
    ("软件工程", "1", "四年", "5800"),
    ("数据科学与大数据技术", "1", "四年", "5800"),
    ("数字媒体技术", "2", "四年", "5800"),
    ("汽车服务工程", "1", "四年", "5800"),
    ("车辆工程", "2", "四年", "5800"),
    ("资源循环科学与工程", "2", "四年", "5800"),
]


def main():
    if not SOURCE_IMAGE.exists():
        raise SystemExit(f"缺少来源图片：{SOURCE_IMAGE}")
    if not SOURCE_ENTRY.exists():
        raise SystemExit(f"缺少官网入口留存页：{SOURCE_ENTRY}")

    rows = []
    for major, plan, duration, fee in ROWS:
        rows.append(
            {
                "学校名称": "江苏理工学院",
                "原始图片": str(SOURCE_IMAGE.relative_to(ROOT)),
                "官网入口页": str(SOURCE_ENTRY.relative_to(ROOT)),
                "类别": "普通类",
                "专业名称": major,
                "科类": "物理类",
                "学制": duration,
                "学费": fee,
                "湖北计划数": plan,
                "提取方法": "official_image_visual_transcription_with_apple_vision_ocr_check",
                "提取局限性": "来源为高校招生官网首页跳转的官方微信公众号图片；未给湖北院校专业组代码和专业代号，需与第19期原页及湖北官方系统对齐。",
            }
        )

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"写出江苏理工学院湖北物理类图片抽取表：{OUTPUT_CSV}")
    print(f"抽取行数：{len(rows)}")


if __name__ == "__main__":
    main()
