#!/usr/bin/env python3
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def ok(label, condition, detail=""):
    status = "OK" if condition else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")
    return condition


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_files():
    ignored = {ROOT / "CHECKSUMS.sha256"}
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path in ignored:
            continue
        files.append(path.relative_to(ROOT).as_posix())
    return set(files)


def main():
    baseline = json.loads((ROOT / "candidate-baseline.json").read_text())
    section = json.loads(
        (ROOT / "data/derived/hubei-2026-physics-section-static-gaokao-cn.json").read_text()
    )
    row_515 = section["data"]["search"]["515"]

    checks = []
    scores = baseline["scores"]
    checks.append(ok("subject scores sum to total", sum(v for k, v in scores.items() if k != "总分") == scores["总分"]))
    checks.append(ok("total score is 515", scores["总分"] == 515))
    checks.append(ok("section JSON 515 cumulative rank", row_515["total"] == "91723", row_515["total"]))
    checks.append(ok("section JSON 515 rank range", row_515["rank_range"] == "90895-91723", row_515["rank_range"]))

    appositive = {str(x["year"]): x for x in row_515["appositive_fraction"]}
    checks.append(ok("2025 equivalent score is 494", appositive["2025"]["score"] == "494", appositive["2025"]["score"]))
    checks.append(ok("2024 equivalent score is 497", appositive["2024"]["score"] == "497", appositive["2024"]["score"]))
    checks.append(ok("2023 equivalent score is 481", appositive["2023"]["score"] == "481", appositive["2023"]["score"]))

    raw_images = list((ROOT / "data/official/hubei-2025-physics-toudang/raw-images").glob("*.jpg"))
    checks.append(ok("2025 official投档线 raw image count", len(raw_images) == 71, str(len(raw_images))))

    parsed_path = ROOT / "data/derived/hubei-2025-physics-toudang-parsed.csv"
    with parsed_path.open(newline="") as f:
        parsed_count = sum(1 for _ in csv.DictReader(f))
    checks.append(ok("parsed 2025投档线 row count >= 3000", parsed_count >= 3000, str(parsed_count)))

    for year, minimum in [("2024", 2700), ("2023", 2800)]:
        pdf = ROOT / f"data/official/hubei-{year}-physics-toudang/hubei-{year}-physics-toudang.pdf"
        checks.append(ok(f"{year} official投档线 PDF exists", pdf.exists() and pdf.stat().st_size > 1000))
        parsed = ROOT / f"data/derived/hubei-{year}-physics-toudang-parsed.csv"
        with parsed.open(newline="") as f:
            count = sum(1 for _ in csv.DictReader(f))
        checks.append(ok(f"parsed {year}投档线 row count >= {minimum}", count >= minimum, str(count)))

    checksum_path = ROOT / "CHECKSUMS.sha256"
    if checksum_path.exists():
        manifest_ok = True
        manifest_rel_paths = set()
        for line in checksum_path.read_text().splitlines():
            expected, rel = line.split(maxsplit=1)
            manifest_rel_paths.add(rel)
            actual = sha256(ROOT / rel)
            if actual != expected:
                print(f"[FAIL] checksum mismatch - {rel}")
                manifest_ok = False
        expected_rel_paths = manifest_files()
        missing = sorted(expected_rel_paths - manifest_rel_paths)
        extra = sorted(manifest_rel_paths - expected_rel_paths)
        for rel in missing:
            print(f"[FAIL] checksum missing file - {rel}")
            manifest_ok = False
        for rel in extra:
            print(f"[FAIL] checksum extra file - {rel}")
            manifest_ok = False
        checks.append(ok("checksum manifest", manifest_ok))
    else:
        checks.append(ok("checksum manifest exists", False))

    if not all(checks):
        raise SystemExit(1)
    print("All baseline checks passed.")


if __name__ == "__main__":
    main()
