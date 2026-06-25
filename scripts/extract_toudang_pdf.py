#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path

import pdfplumber


def clean(value):
    if value is None:
        return ""
    return " ".join(str(value).replace("\n", "").split())


def extract(pdf_path, raw_text_path, parsed_csv_path):
    rows = []
    raw_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            raw_pages.append(f"---PAGE {page_index}\n")
            raw_pages.append(page.extract_text(x_tolerance=1, y_tolerance=3) or "")
            raw_pages.append("\n")
            for table in page.extract_tables() or []:
                for table_row in table:
                    cells = [clean(c) for c in table_row]
                    if not cells or not cells[0]:
                        continue
                    code = cells[0]
                    if not (len(code) >= 6 and code[0].isalpha()):
                        continue
                    score = cells[3] if len(cells) > 3 else ""
                    if not score.isdigit():
                        continue
                    rows.append(
                        {
                            "page": page_index,
                            "code": code,
                            "name": cells[1] if len(cells) > 1 else "",
                            "req": cells[2] if len(cells) > 2 else "",
                            "score": int(score),
                            "语数之和": cells[4] if len(cells) > 4 else "",
                            "语数最高": cells[5] if len(cells) > 5 else "",
                            "外语": cells[6] if len(cells) > 6 else "",
                            "物理": cells[7] if len(cells) > 7 else "",
                            "再选最高": cells[8] if len(cells) > 8 else "",
                            "再选次高": cells[9] if len(cells) > 9 else "",
                            "志愿号": cells[10] if len(cells) > 10 else "",
                            "备注": cells[11] if len(cells) > 11 else "",
                            "row": " | ".join(c for c in cells if c),
                        }
                    )

    raw_text_path.write_text("".join(raw_pages))
    with parsed_csv_path.open("w", newline="") as f:
        fieldnames = [
            "page",
            "code",
            "name",
            "req",
            "score",
            "语数之和",
            "语数最高",
            "外语",
            "物理",
            "再选最高",
            "再选次高",
            "志愿号",
            "备注",
            "row",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"extracted {len(rows)} rows from {pdf_path}")


def main():
    parser = argparse.ArgumentParser(description="Extract Hubei投档线 PDF tables.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--raw-text", type=Path, required=True)
    parser.add_argument("--parsed-csv", type=Path, required=True)
    args = parser.parse_args()
    extract(args.pdf, args.raw_text, args.parsed_csv)


if __name__ == "__main__":
    main()

