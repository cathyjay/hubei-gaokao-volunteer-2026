#!/usr/bin/env python3
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
API_URL = "http://lqcx.blcu.edu.cn/f/ajax_zsjh"
REQUEST_FORM = {
    "ssmc": "湖北",
    "zsnf": "2026",
    "klmc": "物理类",
    "zslx": "普通类",
}
SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"

RAW_OUTPUT = ROOT / "data/external/issue19-c4-c6-official-sources/blcu-2026-hubei-physics-normal.json"
PUBLIC_LEDGER_OUTPUT = ROOT / "data/working/issue19-c4-c6-blcu-official-source-fetch-public-ledger.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-c4-c6-blcu-official-source-fetch-summary.json"


PUBLIC_FIELDS = [
    "C4C6高校官网源抓取ID",
    "来源C4C6执行包ID",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "院校代码",
    "院校名称OCR",
    "官网辅证自动动作",
    "官网URL",
    "请求方式",
    "请求参数摘要",
    "本地留存文件",
    "本地留存文件SHA256",
    "接口state",
    "接口msg",
    "逐专业计划行数",
    "汇总行数",
    "逐专业计划数合计",
    "汇总计划数合计",
    "年份一致性",
    "省份一致性",
    "科类一致性",
    "批次集合SHA256",
    "类别集合SHA256",
    "可核字段",
    "局限性",
    "最终可用",
    "可进入下一阶段",
    "可否进入最终志愿方案",
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


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha_values(values):
    text = "；".join(sorted({str(value) for value in values if str(value).strip()}))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def plan_sum(rows):
    total = 0
    for row in rows:
        try:
            total += int(str(row.get("zsjhs", "")).strip())
        except ValueError:
            pass
    return total


def fetch_json():
    data = urlencode(REQUEST_FORM).encode("utf-8")
    request = Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 issue19-source-retention",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        body = response.read()
    return json.loads(body.decode("utf-8"))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PUBLIC_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    obj = fetch_json()
    RAW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    RAW_OUTPUT.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    data = obj.get("data") if isinstance(obj, dict) else {}
    plan_rows = data.get("zsjhList", []) if isinstance(data, dict) else []
    total_rows = data.get("zsjhTotal", []) if isinstance(data, dict) else []
    row = {
        "C4C6高校官网源抓取ID": "C4C6FETCH-BLCU-A032-2026-HUBEI-PHYSICS-NORMAL",
        "来源C4C6执行包ID": "C4C6PACKET-122c97b755de364b",
        "来源期号": SOURCE_ISSUE,
        "来源PDF_SHA256": SOURCE_PDF_SHA256,
        "数据阶段": "issue19_c4_c6_blcu_official_source_fetch",
        "主表粒度": "高校官网API原始源留存公开账本",
        "院校代码": "A032",
        "院校名称OCR": "北京语言大学",
        "官网辅证自动动作": "C6-继续搜索高校官网2026湖北计划源",
        "官网URL": API_URL,
        "请求方式": "POST application/x-www-form-urlencoded",
        "请求参数摘要": "ssmc=湖北；zsnf=2026；klmc=物理类；zslx=普通类",
        "本地留存文件": str(RAW_OUTPUT.relative_to(ROOT)),
        "本地留存文件SHA256": sha256(RAW_OUTPUT),
        "接口state": str(obj.get("state", "")),
        "接口msg": str(obj.get("msg", "")),
        "逐专业计划行数": str(len(plan_rows)),
        "汇总行数": str(len(total_rows)),
        "逐专业计划数合计": str(plan_sum(plan_rows)),
        "汇总计划数合计": str(plan_sum(total_rows)),
        "年份一致性": "all_2026" if all(item.get("nf") == "2026" for item in plan_rows) else "needs_review",
        "省份一致性": "all_hubei" if all(item.get("ssmc") == "湖北" for item in plan_rows) else "needs_review",
        "科类一致性": "all_physics" if all(item.get("klmc") == "物理类" for item in plan_rows) else "needs_review",
        "批次集合SHA256": sha_values(item.get("zycc", "") for item in plan_rows),
        "类别集合SHA256": sha_values(item.get("zslx", "") for item in plan_rows),
        "可核字段": "年份；省份；科类；类别；批次；专业代号；专业代码；专业名称；计划数；学制；学费；校区；选科",
        "局限性": "高校招生系统API未给湖北院校专业组代码；仍需同第19期PDF原页和湖北官方侧对齐。",
        "最终可用": "false",
        "可进入下一阶段": "false",
        "可否进入最终志愿方案": "false",
        "是否允许作为志愿推荐依据": "false",
        "是否允许自动写回主表": "false",
        "是否允许官网证据替代湖北官方计划": "false",
        "是否允许生成学校专业建议": "false",
        "是否允许写回字段事实": "false",
        "PDF原页核页状态": "pending_manual_pdf_review",
        "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
        "高校官网源抓取状态": "official_school_api_source_retained_not_verified",
        "字段事实写回状态": "blocked_until_pdf_hubei_official_review",
        "下一步": "把原始JSON接入C4/C6结构化候选diff；字段事实仍需PDF原页、湖北官方侧和必要人工复核闭环。",
    }
    write_csv(PUBLIC_LEDGER_OUTPUT, [row])

    summary = {
        "status": "issue19_c4_c6_blcu_official_source_retained_not_final",
        "generated_by": "fetch_issue19_c4_c6_blcu_official_source.py",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "source_api_url": API_URL,
        "request_form": REQUEST_FORM,
        "raw_output": str(RAW_OUTPUT.relative_to(ROOT)),
        "raw_output_sha256": sha256(RAW_OUTPUT),
        "public_ledger": str(PUBLIC_LEDGER_OUTPUT.relative_to(ROOT)),
        "state": obj.get("state"),
        "msg": obj.get("msg"),
        "plan_row_count": len(plan_rows),
        "total_row_count": len(total_rows),
        "plan_sum": plan_sum(plan_rows),
        "total_sum": plan_sum(total_rows),
        "all_year_2026": all(item.get("nf") == "2026" for item in plan_rows),
        "all_province_hubei": all(item.get("ssmc") == "湖北" for item in plan_rows),
        "all_subject_physics": all(item.get("klmc") == "物理类" for item in plan_rows),
        "official_plan_replacement_allowed": False,
        "field_writeback_allowed": False,
        "recommendation_basis_allowed": False,
        "policy": "高校官网API只作辅证和差异发现，不能替代湖北省招办计划或第19期PDF原页。",
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写出北京语言大学官方API原始源：{RAW_OUTPUT.relative_to(ROOT)}")
    print(f"写出公开抓取账本：{PUBLIC_LEDGER_OUTPUT.relative_to(ROOT)}")
    print(f"逐专业计划行数：{len(plan_rows)}")
    print(f"逐专业计划数合计：{plan_sum(plan_rows)}")


if __name__ == "__main__":
    main()
