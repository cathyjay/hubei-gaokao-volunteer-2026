#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATHS = {
    "2023": ROOT / "data/derived/hubei-2023-physics-toudang-parsed.csv",
    "2024": ROOT / "data/derived/hubei-2024-physics-toudang-parsed.csv",
    "2025": ROOT / "data/derived/hubei-2025-physics-toudang-parsed.csv",
}


def main():
    parser = argparse.ArgumentParser(description="筛选湖北首选物理本科普通批投档线解析行。")
    parser.add_argument("--year", nargs="*", default=["2025"], choices=sorted(CSV_PATHS), help="要检索的数据年份。")
    parser.add_argument("--keywords", nargs="*", default=[], help="学校或城市关键词，例如：武汉 成都 西安。")
    parser.add_argument("--min-score", type=int, default=0)
    parser.add_argument("--max-score", type=int, default=750)
    parser.add_argument("--exclude", nargs="*", default=[], help="需要排除的文本片段。")
    args = parser.parse_args()

    rows = []
    for year in args.year:
        with CSV_PATHS[year].open(newline="") as f:
            for row in csv.DictReader(f):
                row["year"] = year
                rows.append(row)

    hits = []
    for row in rows:
        score = int(row["score"])
        text = row["row"]
        if score < args.min_score or score > args.max_score:
            continue
        if args.keywords and not any(k in text for k in args.keywords):
            continue
        if args.exclude and any(k in text for k in args.exclude):
            continue
        hits.append(row)

    hits.sort(key=lambda r: (r["year"], int(r["score"]), r["name"], r["code"]))
    print("year\tscore\tcode\tname\treq\trow")
    for row in hits:
        print(f"{row['year']}\t{row['score']}\t{row['code']}\t{row['name']}\t{row['req']}\t{row['row']}")


if __name__ == "__main__":
    main()
