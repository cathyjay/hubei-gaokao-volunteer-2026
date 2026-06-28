#!/usr/bin/env python3
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
API_URL = "https://admin.zhinengdayi.com/front/enroll/findEnrollPlanDetail"
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"

RAW_DIR = ROOT / "data/external/issue19-next20-official-sources"
PUBLIC_LEDGER_OUTPUT = ROOT / "data/working/issue19-next20-zhinengdayi-official-source-fetch-public-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-next20-zhinengdayi-official-source-fetch-summary.json"

SOURCES = [
    {
        "id": "WHPU-C125-2026-HUBEI-PHYSICS-NORMAL",
        "院校代码": "C125",
        "院校名称": "武汉轻工大学",
        "来源官网入口": "https://zsb.whpu.edu.cn/whpu",
        "request_params": {
            "sCode": "VFUSRX",
            "cityName": "湖北",
            "year": "2026",
            "enrollType": "普通文理",
            "science": "物理类",
            "batch": "本科普通批",
        },
        "raw_output": RAW_DIR / "whpu-2026-hubei-physics-normal.json",
        "可核字段": "年份；省份；科类；批次；专业名；计划数；选科备注",
        "局限性": "官方招生系统API未给湖北院校专业组代码、专业代号、学费或校区；仍需第19期PDF原页和湖北官方侧闭环。",
    },
    {
        "id": "HBNU-C133-2026-HUBEI-PHYSICS-GROUP-NORMAL",
        "院校代码": "C133",
        "院校名称": "湖北师范大学",
        "来源官网入口": "https://zhinengdayi.com/hbnu",
        "request_params": {
            "sCode": "LSPJPH",
            "cityName": "湖北",
            "year": "2026",
            "enrollType": "普通文理",
            "science": "物理组",
            "batch": "-",
        },
        "raw_output": RAW_DIR / "hbnu-2026-hubei-physics-group-normal.json",
        "可核字段": "年份；省份；科类；专业名；计划数；学费备注",
        "局限性": "官方招生系统API批次字段为 '-'，未给湖北院校专业组代码、专业代号、选科或校区；仍需第19期PDF原页和湖北官方侧闭环。",
    },
]

PUBLIC_FIELDS = [
    "next20智能答疑官网源抓取ID",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "院校代码",
    "院校名称",
    "来源官网入口",
    "官网API",
    "请求方式",
    "请求参数摘要",
    "本地留存文件",
    "本地留存文件SHA256",
    "接口success",
    "接口totalRows",
    "逐专业计划行数",
    "逐专业计划数合计",
    "行内totalNum集合SHA256",
    "年份一致性",
    "省份一致性",
    "科类一致性",
    "批次集合SHA256",
    "可核字段",
    "局限性",
    "最终可用",
    "可进入下一阶段",
    "是否可作为定稿依据",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网源抓取状态",
    "字段事实写回状态",
    "下一步",
]

FALSE_FIELDS = [
    "最终可用",
    "可进入下一阶段",
    "是否可作为定稿依据",
    "是否允许作为志愿推荐依据",
    "是否允许自动写回主表",
    "是否允许官网证据替代湖北官方计划",
    "是否允许生成学校专业建议",
    "是否允许写回字段事实",
]


def rel(path):
    return str(path.relative_to(ROOT))


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha_values(values):
    text = "；".join(sorted({str(value) for value in values if str(value).strip()}))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def as_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def fetch_source(source):
    url = API_URL + "?" + urlencode(source["request_params"])
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 issue19-next20-source-retention",
            "Referer": source["来源官网入口"],
        },
    )
    with urlopen(request, timeout=90) as response:
        body = response.read()
    obj = json.loads(body.decode("utf-8"))
    source["raw_output"].parent.mkdir(parents=True, exist_ok=True)
    source["raw_output"].write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return obj


def plan_rows(obj):
    if isinstance(obj, dict) and isinstance(obj.get("data"), list):
        return obj.get("data", [])
    return []


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PUBLIC_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    public_rows = []
    summary_sources = []
    for source in SOURCES:
        obj = fetch_source(source)
        rows = plan_rows(obj)
        plan_sum = sum(as_int(row.get("enrollNum")) for row in rows)
        row = {
            "next20智能答疑官网源抓取ID": f"NEXT20-ZHINENGDAYI-{source['id']}",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": "issue19_next20_zhinengdayi_official_source_fetch",
            "主表粒度": "高校智能答疑官网API原始源留存公开账本",
            "院校代码": source["院校代码"],
            "院校名称": source["院校名称"],
            "来源官网入口": source["来源官网入口"],
            "官网API": API_URL,
            "请求方式": "GET query",
            "请求参数摘要": "；".join(
                f"{key}={value}" for key, value in source["request_params"].items()
            ),
            "本地留存文件": rel(source["raw_output"]),
            "本地留存文件SHA256": sha256(source["raw_output"]),
            "接口success": str(obj.get("success", "")),
            "接口totalRows": str(obj.get("totalRows", "")),
            "逐专业计划行数": str(len(rows)),
            "逐专业计划数合计": str(plan_sum),
            "行内totalNum集合SHA256": sha_values(row.get("totalNum", "") for row in rows),
            "年份一致性": "all_2026" if all(str(row.get("year")) == "2026" for row in rows) else "needs_review",
            "省份一致性": "all_hubei" if all(row.get("cityName") == "湖北" for row in rows) else "needs_review",
            "科类一致性": "all_requested_subject" if all(row.get("science") == source["request_params"]["science"] for row in rows) else "needs_review",
            "批次集合SHA256": sha_values(row.get("batch", "") for row in rows),
            "可核字段": source["可核字段"],
            "局限性": source["局限性"],
            **{field: "false" for field in FALSE_FIELDS},
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "高校官网源抓取状态": "official_school_api_source_retained_not_verified",
            "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
            "下一步": "接入next20官网源探测账本；仅作高校侧double check和冲突发现，不替代湖北官方计划。",
        }
        public_rows.append(row)
        summary_sources.append(
            {
                "院校代码": source["院校代码"],
                "院校名称": source["院校名称"],
                "raw_output": rel(source["raw_output"]),
                "raw_output_sha256": sha256(source["raw_output"]),
                "plan_row_count": len(rows),
                "plan_sum": plan_sum,
                "success": obj.get("success"),
                "totalRows": obj.get("totalRows"),
                "all_year_2026": all(str(row.get("year")) == "2026" for row in rows),
                "all_province_hubei": all(row.get("cityName") == "湖北" for row in rows),
                "subject": source["request_params"]["science"],
                "policy": "高校官网API只作辅证和差异发现，不能替代湖北省招办计划或第19期PDF原页。",
            }
        )

    write_csv(PUBLIC_LEDGER_OUTPUT, public_rows)
    summary = {
        "status": "issue19_next20_zhinengdayi_official_sources_retained_not_final",
        "generated_by": "fetch_issue19_next20_zhinengdayi_official_sources.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_api_url": API_URL,
        "public_ledger": rel(PUBLIC_LEDGER_OUTPUT),
        "source_count": len(SOURCES),
        "plan_row_count": sum(item["plan_row_count"] for item in summary_sources),
        "plan_sum": sum(item["plan_sum"] for item in summary_sources),
        "sources": summary_sources,
        "official_plan_replacement_allowed": False,
        "field_writeback_allowed": False,
        "recommendation_basis_allowed": False,
        "policy": "本摘要只留存高校智能答疑官网API原始源，不能替代第19期原页、湖北官方系统或省招办计划。",
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    public_text = PUBLIC_LEDGER_OUTPUT.read_text(encoding="utf-8", errors="ignore") + SUMMARY_OUTPUT.read_text(
        encoding="utf-8", errors="ignore"
    )
    forbidden = [
        "/Users/",
        "private/",
        "Authorization",
        "Bearer ",
        "Cookie",
        "access_token",
        "password",
        "secret",
        "人工读数",
        "已确认",
        "已核准",
        "最终推荐",
        "最终方案",
        "可填报",
        "可排序",
    ]
    if any(token in public_text for token in forbidden):
        raise SystemExit("next20智能答疑公开账本包含禁止公开内容")
    print(f"写出 next20 智能答疑官网API源公开账本：{rel(PUBLIC_LEDGER_OUTPUT)}")
    print(f"写出摘要：{rel(SUMMARY_OUTPUT)}")
    print(f"抓取学校数：{len(SOURCES)}，逐专业计划行数：{summary['plan_row_count']}，计划数合计：{summary['plan_sum']}")


if __name__ == "__main__":
    main()
