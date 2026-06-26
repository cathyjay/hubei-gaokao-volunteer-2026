#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, parse, request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://zspt.hubzs.com.cn"
DEFAULT_RAW_DIR = ROOT / "private/hubei-plan-platform/raw"
DEFAULT_OUTPUT_CSV = ROOT / "data/working/hubei-2026-official-platform-admission-detail.csv"
DEFAULT_SUMMARY = ROOT / "data/working/hubei-2026-official-platform-admission-detail-summary.json"

DICT_TYPES = [
    "pcdm",
    "kldm",
    "ssdm",
    "bxxzdm",
    "sxzylbdm",
    "sxjhlbdm",
    "zyxkkmdm",
]

OUTPUT_FIELDS = [
    "抓取批次ID",
    "来源",
    "年份",
    "批次代码",
    "批次名称",
    "科类代码",
    "科类名称",
    "页码",
    "页内序号",
    "原始行类型",
    "是否真实招生明细",
    "是否0明细占位",
    "院校代码",
    "院校代号",
    "院校名称",
    "院校及院校代号",
    "院校专业组代码",
    "院校专业组名称及备注",
    "专业代号",
    "专业名称及备注",
    "再选/专业科目要求",
    "人数",
    "年学费（元）",
    "办学地点",
    "招生详情链接",
    "近两年参考计划",
    "原始行SHA256",
    "原始行JSON",
]


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_token():
    token = os.environ.get("HUBEI_PLAN_TOKEN") or os.environ.get("HUBEI_PLAN_AUTH_TOKEN")
    if not token:
        return ""
    token = token.strip()
    if token.lower().startswith("bearer "):
        return token
    return f"Bearer {token}"


def api_get(base_url, endpoint, params=None, token="", timeout=30):
    params = params or {}
    query = parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
    url = f"{base_url.rstrip('/')}{endpoint}"
    if query:
        url = f"{url}?{query}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "gaokao-volunteer-2026-hubei-data-audit/1.0",
        "Referer": f"{base_url.rstrip('/')}/",
    }
    if token:
        headers["Authorization"] = token
    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return {
                "url": url,
                "status": resp.status,
                "headers": dict(resp.headers.items()),
                "body": body.decode("utf-8", errors="replace"),
            }
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "url": url,
            "status": exc.code,
            "headers": dict(exc.headers.items()),
            "body": body,
        }


def parse_json_response(response):
    try:
        return json.loads(response["body"])
    except json.JSONDecodeError as exc:
        raise ValueError(f"接口返回不是 JSON：{response['url']} status={response['status']}") from exc


def payload_rows(obj):
    candidates = [
        obj,
        obj.get("data") if isinstance(obj, dict) else None,
    ]
    for candidate in list(candidates):
        if isinstance(candidate, dict):
            candidates.extend(
                candidate.get(key)
                for key in ["rows", "records", "list", "data"]
                if key in candidate
            )
    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate
        if isinstance(candidate, dict):
            for key in ["rows", "records", "list"]:
                if isinstance(candidate.get(key), list):
                    return candidate[key]
    return []


def payload_total(obj, fallback_count):
    for container in [obj, obj.get("data") if isinstance(obj, dict) else None]:
        if not isinstance(container, dict):
            continue
        for key in ["total", "count", "rowCount"]:
            value = container.get(key)
            if value is None:
                continue
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
    return fallback_count


def response_code(obj):
    if isinstance(obj, dict) and "code" in obj:
        return str(obj.get("code"))
    return ""


def fail_if_auth_error(obj, endpoint):
    if response_code(obj) == "401":
        msg = obj.get("msg", "令牌无效或为空")
        raise SystemExit(f"{endpoint} 返回 401：{msg}。请用 HUBEI_PLAN_TOKEN 环境变量传入登录态，不要写入仓库。")


def save_raw_json(raw_dir, name, response, obj, metadata):
    raw_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": metadata,
        "http_status": response["status"],
        "url_sha256": sha256_text(response["url"]),
        "response_headers": response.get("headers", {}),
        "body_sha256": sha256_text(response["body"]),
        "json": obj,
    }
    path = raw_dir / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def dict_label(row):
    for key in ["dictLabel", "label", "mc", "name", "text", "pcmc", "klmc"]:
        value = row.get(key) if isinstance(row, dict) else None
        if value:
            return str(value)
    return ""


def dict_value(row):
    for key in ["dictValue", "value", "dm", "code", "id", "pcdm", "kldm"]:
        value = row.get(key) if isinstance(row, dict) else None
        if value is not None and str(value) != "":
            return str(value)
    return ""


def find_dict_value(rows, contains, dict_name):
    contains = (contains or "").strip()
    if not contains:
        return ""
    matches = [row for row in rows if contains in dict_label(row)]
    if len(matches) == 1:
        return dict_value(matches[0])
    if not matches:
        raise SystemExit(f"{dict_name} 字典中找不到包含“{contains}”的项，请改用显式代码。")
    labels = "；".join(dict_label(row) for row in matches)
    raise SystemExit(f"{dict_name} 字典中“{contains}”匹配多个项：{labels}。请改用显式代码。")


def first_value(row, keys):
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def compact_row_json(row, include_raw):
    if not include_raw:
        return ""
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def raw_row_hash(row):
    return sha256_text(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def emit_placeholder(batch_id, year, params, page_num, row_num, school, group, include_raw):
    raw = {
        "type": "ZERO_DETAIL_PLACEHOLDER",
        "school": school,
        "group": group,
        "reason": "院校专业组行后未见专业行，保留组线索，需人工核验。",
    }
    return {
        "抓取批次ID": batch_id,
        "来源": "湖北招生数智综合平台 /prod-api/planQuery/plan/group",
        "年份": str(year),
        "批次代码": params.get("pcdm", ""),
        "批次名称": group.get("pcmc", "") or school.get("pcmc", ""),
        "科类代码": params.get("kldm", ""),
        "科类名称": group.get("klmc", "") or school.get("klmc", ""),
        "页码": str(page_num),
        "页内序号": str(row_num),
        "原始行类型": "ZERO_DETAIL_PLACEHOLDER",
        "是否真实招生明细": "false",
        "是否0明细占位": "true",
        "院校代码": school.get("院校代码", ""),
        "院校代号": school.get("院校代号", ""),
        "院校名称": school.get("院校名称", ""),
        "院校及院校代号": school.get("院校及院校代号", ""),
        "院校专业组代码": group.get("院校专业组代码", ""),
        "院校专业组名称及备注": group.get("院校专业组名称及备注", ""),
        "专业代号": "",
        "专业名称及备注": "",
        "再选/专业科目要求": "",
        "人数": "",
        "年学费（元）": "",
        "办学地点": group.get("办学地点", ""),
        "招生详情链接": group.get("招生详情链接", ""),
        "近两年参考计划": group.get("近两年参考计划", ""),
        "原始行SHA256": raw_row_hash(raw),
        "原始行JSON": compact_row_json(raw, include_raw),
    }


def normalize_plan_rows(rows, *, batch_id, year, params, page_num, include_raw):
    output = []
    school = {}
    group = {}
    group_has_major = True
    row_num = 0

    def flush_group_placeholder():
        if group and not group_has_major:
            output.append(
                emit_placeholder(
                    batch_id,
                    year,
                    params,
                    page_num,
                    row_num,
                    school,
                    group,
                    include_raw,
                )
            )

    for source_row in rows:
        row_num += 1
        row_type = first_value(source_row, ["type", "rowType", "lx"])
        row_type_upper = row_type.upper()
        code_or_major = first_value(source_row, ["yxzyz_zydh", "zydh", "zsdh", "code"])
        name_or_remark = first_value(source_row, ["yxzyz_zymc_bz", "zymc", "mc", "name"])

        if row_type_upper == "YX":
            flush_group_placeholder()
            school = {
                "院校代码": first_value(source_row, ["yxdm", "yxcode", "yxId"]),
                "院校代号": code_or_major,
                "院校名称": name_or_remark,
                "院校及院校代号": f"{code_or_major} {name_or_remark}".strip(),
                "pcmc": first_value(source_row, ["pcmc"]),
                "klmc": first_value(source_row, ["klmc"]),
            }
            group = {}
            group_has_major = True
            continue

        if row_type_upper == "ZYZ":
            flush_group_placeholder()
            group = {
                "院校专业组代码": code_or_major,
                "院校专业组名称及备注": name_or_remark,
                "办学地点": first_value(source_row, ["bxdd"]),
                "招生详情链接": first_value(source_row, ["zsxx"]),
                "近两年参考计划": first_value(source_row, ["jnzs"]),
                "pcmc": first_value(source_row, ["pcmc"]),
                "klmc": first_value(source_row, ["klmc"]),
            }
            group_has_major = False
            continue

        if row_type_upper != "ZY":
            continue

        group_has_major = True
        raw_json = compact_row_json(source_row, include_raw)
        output.append(
            {
                "抓取批次ID": batch_id,
                "来源": "湖北招生数智综合平台 /prod-api/planQuery/plan/group",
                "年份": str(year),
                "批次代码": params.get("pcdm", ""),
                "批次名称": first_value(source_row, ["pcmc"]) or group.get("pcmc", "") or school.get("pcmc", ""),
                "科类代码": params.get("kldm", ""),
                "科类名称": first_value(source_row, ["klmc"]) or group.get("klmc", "") or school.get("klmc", ""),
                "页码": str(page_num),
                "页内序号": str(row_num),
                "原始行类型": row_type,
                "是否真实招生明细": "true",
                "是否0明细占位": "false",
                "院校代码": first_value(source_row, ["yxdm", "yxcode", "yxId"]) or school.get("院校代码", ""),
                "院校代号": school.get("院校代号", ""),
                "院校名称": school.get("院校名称", ""),
                "院校及院校代号": school.get("院校及院校代号", ""),
                "院校专业组代码": group.get("院校专业组代码", ""),
                "院校专业组名称及备注": group.get("院校专业组名称及备注", ""),
                "专业代号": code_or_major,
                "专业名称及备注": name_or_remark,
                "再选/专业科目要求": first_value(source_row, ["zxkmyq", "xkkmyq", "xkyq"]),
                "人数": first_value(source_row, ["rs", "jhrs", "planNum"]),
                "年学费（元）": first_value(source_row, ["xf", "sf", "tuition"]),
                "办学地点": first_value(source_row, ["bxdd"]) or group.get("办学地点", ""),
                "招生详情链接": first_value(source_row, ["zsxx"]) or group.get("招生详情链接", ""),
                "近两年参考计划": first_value(source_row, ["jnzs"]) or group.get("近两年参考计划", ""),
                "原始行SHA256": raw_row_hash(source_row),
                "原始行JSON": raw_json,
            }
        )

    flush_group_placeholder()
    return output


def write_output_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fetch_dicts(base_url, year, token, raw_dir, batch_id):
    dicts = {}
    for dict_type in DICT_TYPES:
        response = api_get(base_url, f"/prod-api/planQuery/dict/{dict_type}/{year}", token=token)
        obj = parse_json_response(response)
        fail_if_auth_error(obj, f"/planQuery/dict/{dict_type}/{year}")
        dicts[dict_type] = payload_rows(obj)
        save_raw_json(
            raw_dir,
            f"{batch_id}-dict-{dict_type}.json",
            response,
            obj,
            {
                "fetched_at_utc": utc_timestamp(),
                "endpoint": f"/prod-api/planQuery/dict/{dict_type}/{year}",
                "token_redacted": True,
                "ksh_redacted": True,
            },
        )
    return dicts


def build_params(args, dicts):
    pcdm = args.batch_code or find_dict_value(dicts.get("pcdm", []), args.batch_label_contains, "批次")
    kldm = args.subject_code or find_dict_value(dicts.get("kldm", []), args.subject_label_contains, "科类")
    params = {
        "nf": str(args.year),
        "pageSize": str(args.page_size),
        "pcdm": pcdm,
        "kldm": kldm,
    }
    if args.school_keyword:
        params["yxglzc"] = args.school_keyword.upper()
    if args.group_code:
        params["yxzyzdh"] = args.group_code.upper()
    if args.major_keyword:
        params["zyglzc1"] = args.major_keyword
    if args.student_subject_mode:
        params["xkkmglfs"] = args.student_subject_mode
    if args.student_subject_codes:
        params["xkkmdmlb"] = args.student_subject_codes
    if args.ksh:
        params["ksh"] = "__REDACTED_KSH__"
    return params


def fetch_pages(args, token, params, raw_dir, batch_id):
    all_rows = []
    page_summaries = []
    total = None
    page_num = 1
    while True:
        query_params = dict(params)
        query_params["pageNum"] = str(page_num)
        real_params = dict(query_params)
        if args.ksh:
            real_params["ksh"] = args.ksh
        response = api_get(args.base_url, "/prod-api/planQuery/plan/group", real_params, token=token)
        obj = parse_json_response(response)
        fail_if_auth_error(obj, "/planQuery/plan/group")
        rows = payload_rows(obj)
        total = payload_total(obj, total if total is not None else len(rows))
        save_raw_json(
            raw_dir,
            f"{batch_id}-plan-group-page-{page_num:04d}.json",
            response,
            obj,
            {
                "fetched_at_utc": utc_timestamp(),
                "endpoint": "/prod-api/planQuery/plan/group",
                "query_params": query_params,
                "token_redacted": True,
                "ksh_redacted": bool(args.ksh),
            },
        )
        normalized = normalize_plan_rows(
            rows,
            batch_id=batch_id,
            year=args.year,
            params=params,
            page_num=page_num,
            include_raw=args.include_raw_json_in_csv,
        )
        all_rows.extend(normalized)
        page_summaries.append(
            {
                "page_num": page_num,
                "raw_row_count": len(rows),
                "normalized_detail_row_count": len(normalized),
                "response_body_sha256": sha256_text(response["body"]),
            }
        )
        print(
            f"page {page_num}: raw_rows={len(rows)} normalized_details={len(normalized)} total={total}",
            file=sys.stderr,
        )
        if not rows:
            break
        if args.max_pages and page_num >= args.max_pages:
            break
        if total is not None and page_num * args.page_size >= total:
            break
        page_num += 1
        time.sleep(args.sleep_seconds)
    return all_rows, page_summaries, total


def dry_run_contract():
    print(
        json.dumps(
            {
                "base_url": DEFAULT_BASE_URL,
                "auth": {
                    "cookie_name": "Admin-Token",
                    "request_header": "Authorization: Bearer <Admin-Token>",
                    "env_vars": ["HUBEI_PLAN_TOKEN", "HUBEI_PLAN_AUTH_TOKEN"],
                    "redaction": "脚本不打印、不保存 token；ksh 只写入私有原始请求元数据的 redacted 标识。",
                },
                "main_endpoint": "/prod-api/planQuery/plan/group",
                "dict_endpoint": "/prod-api/planQuery/dict/{dictType}/{year}",
                "dict_types": DICT_TYPES,
                "main_params": {
                    "nf": "2026",
                    "pageNum": 1,
                    "pageSize": 200,
                    "pcdm": "批次代码，建议用 --batch-label-contains 本科普通批 自动从字典解析",
                    "kldm": "科类代码，建议用 --subject-label-contains 物理 自动从字典解析",
                    "yxglzc": "可选，院校关键词",
                    "yxzyzdh": "可选，院校专业组代码",
                    "zyglzc1": "可选，专业关键词",
                    "ksh": "可选，只通过 --ksh 或 HUBEI_PLAN_KSH 传入，不写公开文件",
                },
                "normalized_grain": "一行一个招生专业；若专业组无专业行，仅输出 0 明细占位。",
                "private_raw_dir_default": str(DEFAULT_RAW_DIR.relative_to(ROOT)),
                "public_csv_default": str(DEFAULT_OUTPUT_CSV.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def parse_args():
    parser = argparse.ArgumentParser(description="抓取湖北招生数智综合平台 2026 招生计划逐专业明细。")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--batch-code", default="")
    parser.add_argument("--batch-label-contains", default="本科普通批")
    parser.add_argument("--subject-code", default="")
    parser.add_argument("--subject-label-contains", default="物理")
    parser.add_argument("--school-keyword", default="")
    parser.add_argument("--group-code", default="")
    parser.add_argument("--major-keyword", default="")
    parser.add_argument("--student-subject-mode", default="")
    parser.add_argument("--student-subject-codes", default="")
    parser.add_argument("--ksh", default=os.environ.get("HUBEI_PLAN_KSH", ""))
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--max-pages", type=int, default=0)
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--output-summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--include-raw-json-in-csv", action="store_true")
    parser.add_argument("--dry-run-contract", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.dry_run_contract:
        dry_run_contract()
        return

    token = read_token()
    if not token:
        raise SystemExit(
            "缺少 HUBEI_PLAN_TOKEN/HUBEI_PLAN_AUTH_TOKEN。请从已登录平台会话提取 Admin-Token，"
            "只放在环境变量中运行，不要写入仓库或命令历史。"
        )

    raw_dir = args.raw_dir
    if not raw_dir.is_absolute():
        raw_dir = ROOT / raw_dir
    output_csv = args.output_csv if args.output_csv.is_absolute() else ROOT / args.output_csv
    output_summary = args.output_summary if args.output_summary.is_absolute() else ROOT / args.output_summary
    batch_id = f"hubei-plan-platform-{args.year}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    dicts = fetch_dicts(args.base_url, args.year, token, raw_dir, batch_id)
    params = build_params(args, dicts)
    rows, page_summaries, total = fetch_pages(args, token, params, raw_dir, batch_id)
    write_output_csv(output_csv, rows)

    summary = {
        "status": "hubei_official_platform_plan_detail_fetched_not_final_until_crosschecked",
        "generated_by": Path(__file__).name,
        "fetched_at_utc": utc_timestamp(),
        "batch_id": batch_id,
        "source": args.base_url,
        "endpoint": "/prod-api/planQuery/plan/group",
        "year": args.year,
        "query_params_public": params,
        "token_redacted": True,
        "ksh_redacted": bool(args.ksh),
        "private_raw_dir": str(raw_dir.relative_to(ROOT)) if raw_dir.is_relative_to(ROOT) else str(raw_dir),
        "output_csv": str(output_csv.relative_to(ROOT)) if output_csv.is_relative_to(ROOT) else str(output_csv),
        "row_count": len(rows),
        "real_admission_detail_count": sum(row["是否真实招生明细"] == "true" for row in rows),
        "zero_detail_placeholder_count": sum(row["是否0明细占位"] == "true" for row in rows),
        "raw_total_from_api": total,
        "page_count": len(page_summaries),
        "page_summaries": page_summaries,
        "output_csv_sha256": sha256_file(output_csv),
        "fidelity_note": "公开 CSV 为逐专业规范化表；私有 raw JSON 保留接口原始响应和响应哈希。进入最终方案前仍需第19期原页、湖北官方系统/省招办计划、高校官网/章程和家庭接受度闭环。",
    }
    output_summary.parent.mkdir(parents=True, exist_ok=True)
    output_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写出 {output_csv.relative_to(ROOT)}：{len(rows)} 行")
    print(f"写出 {output_summary.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
