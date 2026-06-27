#!/usr/bin/env python3
import hashlib
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_DIR = ROOT / "data/official/hubei-2026-admission-plan-platform"
OUTPUT = ROOT / "data/working/issue19-official-public-entry-live-recheck.json"

PAGES = [
    {
        "key": "official_plan_page",
        "name": "湖北教育考试网 2026 招生计划页面",
        "url": "http://www.hbccks.cn/html/gkzsjh/2026-05/142888.html",
        "preserved_copy": OFFICIAL_DIR / "hbccks-2026-plan-page.html",
        "contains_checks": {
            "contains_2026_plan_title": "2026年普通高等学校招生计划",
            "contains_waiting_notice": ["持续更新中", "敬请期待"],
        },
    },
    {
        "key": "official_plan_index",
        "name": "湖北教育考试网招生计划索引",
        "url": "http://www.hbccks.cn/html/gkgzzt/gkzsjh/",
        "preserved_copy": OFFICIAL_DIR / "hbccks-plan-index.html",
        "contains_checks": {
            "contains_2026_plan_link": "2026年普通高等学校招生计划",
            "contains_waiting_notice": ["持续更新中", "敬请期待"],
        },
    },
    {
        "key": "zspt_platform_home",
        "name": "湖北招生数智综合平台首页",
        "url": "https://zspt.hubzs.com.cn",
        "preserved_copy": OFFICIAL_DIR / "index-live-20260628.html",
        "contains_checks": {},
    },
]

PROBES = [
    {
        "key": "plan_nfs_no_login",
        "name": "平台计划年份接口无登录探针",
        "url": "https://zspt.hubzs.com.cn/prod-api/planQuery/plan/nfs",
        "preserved_copy": OFFICIAL_DIR / "api-probes/planQuery-plan-nfs-no-token.json",
    },
    {
        "key": "plan_yxlist_2026_wuhan_no_login",
        "name": "平台学校检索接口无登录探针",
        "url": "https://zspt.hubzs.com.cn/prod-api/planQuery/plan/yxList?nf=2026&keyword=%E6%AD%A6%E6%B1%89",
        "preserved_copy": OFFICIAL_DIR / "api-probes/planQuery-plan-yxList-2026-wuhan-no-token.json",
    },
    {
        "key": "plan_group_current_no_login",
        "name": "平台计划分组接口无登录探针",
        "url": "https://zspt.hubzs.com.cn/prod-api/planQuery/plan/group",
        "preserved_copy": OFFICIAL_DIR / "api-probes/planQuery-plan-group-current-no-token.json",
    },
    {
        "key": "plan_student_no_login",
        "name": "平台考生计划接口无登录探针",
        "url": "https://zspt.hubzs.com.cn/prod-api/planQuery/plan/student",
        "preserved_copy": OFFICIAL_DIR / "api-probes/planQuery-plan-student-no-token.json",
    },
    {
        "key": "plan_dict_batch_2026_no_login",
        "name": "平台批次字典接口无登录探针",
        "url": "https://zspt.hubzs.com.cn/prod-api/planQuery/dict/pcdm?nf=2026",
        "preserved_copy": OFFICIAL_DIR / "api-probes/planQuery-dict-pcdm-2026-no-token.json",
    },
]


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def title_of(text):
    match = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def fetch(url):
    marker = "__ISSUE19_CURL_META__"
    command = [
        "curl",
        "-L",
        "--silent",
        "--show-error",
        "--max-time",
        "20",
        "--user-agent",
        (
            "Mozilla/5.0 issue19-official-live-recheck "
            "(public metadata only)"
        ),
        "--write-out",
        f"%{{stderr}}{marker}%{{http_code}}\t%{{url_effective}}\t%{{content_type}}",
        url,
    ]
    result = subprocess.run(command, check=False, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="ignore").strip()
        raise RuntimeError(f"curl failed for {url}: {stderr}")
    stdout = result.stdout
    stderr = result.stderr
    if marker.encode("utf-8") not in stderr:
        raise RuntimeError(f"curl metadata marker missing for {url}")
    _, meta = stderr.rsplit(marker.encode("utf-8"), 1)
    parts = meta.decode("utf-8", errors="ignore").strip().split("\t", 2)
    if len(parts) != 3:
        raise RuntimeError(f"curl metadata parse failed for {url}: {parts}")
    status, effective_url, content_type = parts
    return {
        "http_status": int(status),
        "effective_url": effective_url,
        "content_type": content_type,
        "body": stdout,
    }


def contains_value(text, expected):
    if isinstance(expected, list):
        return any(item in text for item in expected)
    return expected in text


def page_result(config):
    fetched = fetch(config["url"])
    body = fetched.pop("body")
    text = body.decode("utf-8", errors="ignore")
    live_sha = sha256_bytes(body)
    preserved = config["preserved_copy"]
    preserved_sha = sha256_file(preserved)
    result = {
        "name": config["name"],
        "url": config["url"],
        "method": "GET",
        **fetched,
        "body_length_bytes": len(body),
        "live_sha256": live_sha,
        "title": title_of(text),
        "preserved_copy": preserved.relative_to(ROOT).as_posix(),
        "preserved_sha256": preserved_sha,
        "same_as_preserved_copy": live_sha == preserved_sha,
        "can_finalize": False,
    }
    for field, expected in config.get("contains_checks", {}).items():
        result[field] = contains_value(text, expected)
    return result


def probe_result(config):
    fetched = fetch(config["url"])
    body = fetched.pop("body")
    text = body.decode("utf-8", errors="ignore").strip()
    try:
        response_json = json.loads(text)
    except json.JSONDecodeError:
        response_json = {}
    preserved = config["preserved_copy"]
    live_sha = sha256_bytes(body)
    preserved_sha = sha256_file(preserved)
    is_blocked = response_json.get("code") == 401 or response_json.get("msg") == "令牌不能为空"
    return {
        "name": config["name"],
        "url": config["url"],
        "method": "GET",
        **fetched,
        "body_length_bytes": len(body),
        "live_sha256": live_sha,
        "preserved_copy": preserved.relative_to(ROOT).as_posix(),
        "preserved_sha256": preserved_sha,
        "same_as_preserved_copy": live_sha == preserved_sha,
        "response": response_json,
        "is_unauthenticated_blocked": is_blocked,
        "can_finalize": False,
    }


def main():
    checked_at = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    page_results = {config["key"]: page_result(config) for config in PAGES}
    probe_results = {config["key"]: probe_result(config) for config in PROBES}
    all_probe_blocked = all(
        item["is_unauthenticated_blocked"] for item in probe_results.values()
    )
    status = {
        "status": "issue19_official_public_entry_live_recheck_not_final",
        "generated_by": "build_issue19_official_public_entry_live_recheck.py",
        "checked_at": checked_at,
        "output_file": "data/working/issue19-official-public-entry-live-recheck.json",
        "privacy_boundary": "只保存公开入口元数据、SHA、标题和无登录探针结果；不保存网页登录凭证、个人身份信息或完整 HTML 正文。",
        "row_grain_policy": "本文件只复核官方入口/接口可得性，不替代一行一个招生专业的第19期底座。",
        "page_results": page_results,
        "probe_results": probe_results,
        "current_conclusion": {
            "can_get_official_structured_plan_without_login": False,
            "can_finalize_admission_plan_from_public_entry": False,
            "official_plan_page_still_waiting": page_results["official_plan_page"].get(
                "contains_waiting_notice"
            )
            is True,
            "platform_public_home_accessible": page_results["zspt_platform_home"].get(
                "http_status"
            )
            == 200,
            "all_platform_probes_blocked_without_login": all_probe_blocked,
            "meaning": "截至本次活体复查，能自动取得的是官方入口状态，不是可逐字段定稿的湖北官方结构化招生计划。",
        },
        "fallback_when_unavailable": {
            "automated_first": [
                "自动复跑高校官网/API/XLSX/PDF/图片计划源，按专业行ID比对专业名、计划数、学费、选科、校区、备注和章程限制。",
                "把一致项标记为高校侧辅证，把冲突、缺口、未匹配和低置信度项升级到人工核页。",
                "保留高校侧来源 SHA、抽取方式、字段覆盖和冲突类型，但不把高校官网替代湖北省招办计划。",
            ],
            "minimal_manual": [
                "最终候选、冲稳保边界、B0/B1优先组、计划数冲突、官网未匹配、字段空缺但进入候选的专业必须人工回看第19期原页。",
                "低风险强辅证只做分层抽检；抽检失败后升级同页列、同校或同专业组100%人工核验。",
                "人工只签认 PDF 原页读数、湖北官方侧可得时的字段值、高校辅证值、家庭接受度和调剂结论，不承担全量无差别逐字段重录。",
            ],
        },
    }
    OUTPUT.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
