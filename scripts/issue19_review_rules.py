#!/usr/bin/env python3
import csv
import hashlib
from pathlib import Path


PREFERENCE_TAG_LABELS = {
    "priority_1_digital_media": "数字媒体技术",
    "priority_2_computer": "计算机类相关",
    "priority_3_teacher": "师范类相关",
}

RISK_TAG_LABELS = {
    "rejected_medical": "医学/护理等排除方向",
    "high_fee_or_coop": "中外合作或高收费",
    "tuition_over_15000": "学费超过当前上限",
    "body_or_exam_limit": "体检或色觉限制",
    "language_or_single_subject": "语种或单科限制",
    "special_plan_or_direction": "专项/预科/定向等特殊类型",
}

GROUP_REVIEW_RISK_TAGS = set(RISK_TAG_LABELS)
DEFAULT_EXCLUDE_RISK_TAGS = {"high_fee_or_coop", "tuition_over_15000"}
PAUSE_REVIEW_RISK_TAGS = {
    "rejected_medical",
    "body_or_exam_limit",
    "language_or_single_subject",
    "special_plan_or_direction",
}
HARD_RISK_LEVEL_TAGS = {
    "rejected_medical",
    "high_fee_or_coop",
    "tuition_over_15000",
    "special_plan_or_direction",
}
LIMIT_RISK_LEVEL_TAGS = {"body_or_exam_limit", "language_or_single_subject"}
RISK_LEVEL_ORDER = {"未触发硬风险": 0, "限制风险": 1, "硬风险": 2}


def split_tags(value):
    if not value:
        return set()
    return {part.strip() for part in str(value).replace("；", ";").split(";") if part.strip()}


def as_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def tags_with_tuition_limit(tags, tuition, tuition_limit):
    result = set(tags)
    if tuition and tuition > tuition_limit:
        result.add("tuition_over_15000")
    return result


def review_risk_tags(tags, tuition=None, tuition_limit=None):
    if tuition_limit is not None:
        tags = tags_with_tuition_limit(tags, tuition, tuition_limit)
    return set(tags) & GROUP_REVIEW_RISK_TAGS


def risk_labels(tags):
    return "；".join(RISK_TAG_LABELS[tag] for tag in sorted(tags) if tag in RISK_TAG_LABELS)


def risk_level(tags):
    if tags & HARD_RISK_LEVEL_TAGS:
        return "硬风险"
    if tags & LIMIT_RISK_LEVEL_TAGS:
        return "限制风险"
    return "未触发硬风险"


def combine_risk_levels(*levels):
    return max(levels, key=lambda level: RISK_LEVEL_ORDER.get(level, -1))


def csv_row_count(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        return sum(1 for _ in csv.DictReader(f))


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def input_snapshot(root, paths):
    snapshot = []
    for path in paths:
        path = Path(path)
        item = {
            "path": str(path.relative_to(root)),
            "sha256": sha256_file(path),
        }
        if path.suffix == ".csv":
            item["row_count"] = csv_row_count(path)
        snapshot.append(item)
    return snapshot
