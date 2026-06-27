#!/usr/bin/env python3
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

OFFICIAL_DIR = ROOT / "data/official/hubei-2026-admission-plan-platform"
PLAN_PAGE = OFFICIAL_DIR / "hbccks-2026-plan-page.html"
PLAN_INDEX = OFFICIAL_DIR / "hbccks-plan-index.html"
ZSPT_HOME = OFFICIAL_DIR / "index-live-20260627.html"
ZSPT_NFS_PROBE = OFFICIAL_DIR / "api-probes/planQuery-plan-nfs-no-token.json"
ZSPT_YXLIST_PROBE = OFFICIAL_DIR / "api-probes/planQuery-plan-yxList-2026-wuhan-no-token.json"
OUTPUT = ROOT / "data/working/issue19-official-public-entry-status.json"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path):
    return path.read_text(encoding="utf-8", errors="ignore")


def title_of(html):
    match = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def probe_result(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "local_copy": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(path),
        "response": data,
        "is_unauthenticated_blocked": data.get("code") == 401 or data.get("msg") == "令牌不能为空",
    }


def main():
    plan_page_html = read_text(PLAN_PAGE)
    plan_index_html = read_text(PLAN_INDEX)
    zspt_home_html = read_text(ZSPT_HOME)

    status = {
        "status": "issue19_official_public_entry_status_not_final",
        "generated_by": "build_issue19_official_public_entry_status_snapshot.py",
        "checked_at": "2026-06-27",
        "output_file": "data/working/issue19-official-public-entry-status.json",
        "row_grain_policy": "本状态快照只判断官方公开入口可用性；招生计划底座仍以逐专业招生明细为主粒度。",
        "official_plan_page": {
            "url": "http://www.hbccks.cn/html/gkzsjh/2026-05/142888.html",
            "local_copy": PLAN_PAGE.relative_to(ROOT).as_posix(),
            "sha256": sha256(PLAN_PAGE),
            "title": title_of(plan_page_html),
            "contains_2026_plan_title": "2026年普通高等学校招生计划" in plan_page_html,
            "contains_waiting_notice": "持续更新中" in plan_page_html or "敬请期待" in plan_page_html,
            "live_check_note": "2026-06-27 使用公开 HTTP 拉取返回 200；SHA256 与本地留存一致。",
            "foundation_meaning": "页面公开但正文仍含持续更新/敬请期待提示，不能单独作为最终招生计划底稿。",
        },
        "official_plan_index": {
            "url": "http://www.hbccks.cn/html/gkgzzt/gkzsjh/",
            "local_copy": PLAN_INDEX.relative_to(ROOT).as_posix(),
            "sha256": sha256(PLAN_INDEX),
            "title": title_of(plan_index_html),
            "contains_2026_plan_link": "2026年普通高等学校招生计划" in plan_index_html,
            "contains_waiting_notice": "持续更新中" in plan_index_html or "敬请期待" in plan_index_html,
            "live_check_note": "2026-06-27 使用公开 HTTP 拉取返回 200；SHA256 与本地留存一致。",
            "foundation_meaning": "索引能证明官方计划入口存在，但不能替代第19期逐专业明细和官方系统字段核验。",
        },
        "zspt_platform": {
            "url": "https://zspt.hubzs.com.cn",
            "local_copy": ZSPT_HOME.relative_to(ROOT).as_posix(),
            "sha256": sha256(ZSPT_HOME),
            "title": title_of(zspt_home_html),
            "unauthenticated_probe_results": [
                probe_result(ZSPT_NFS_PROBE),
                probe_result(ZSPT_YXLIST_PROBE),
            ],
            "foundation_meaning": "平台前端和接口线索已留存；无登录请求返回 401，不能用无登录数据替代考生端官方查询结果。",
        },
        "current_foundation_boundary": {
            "can_support": [
                "确认湖北官方 2026 招生计划公开入口与平台入口存在。",
                "确认无登录平台接口不能直接取得可定稿数据。",
                "支撑 OCR 底座继续做逐专业保真核验任务。",
            ],
            "cannot_support": [
                "不能直接生成最终志愿方案。",
                "不能把 OCR 字段候选自动写回最终表。",
                "不能把高校官网或第三方数据替代湖北省招办公布计划。",
            ],
            "required_before_final": [
                "逐专业核第19期PDF原页或纸质版原页。",
                "逐专业核湖北官方系统/省招办计划字段。",
                "对候选院校专业组核官网/招生章程、学费、校区、特殊要求和调剂范围。",
                "用近三年投档线只做冲稳保风险判断，不能替代2026招生计划。",
            ],
        },
    }
    OUTPUT.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
