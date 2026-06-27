#!/usr/bin/env python3
import csv
import hashlib
import html
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FIELD_CONFIRM_LEDGER = ROOT / "data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv"
PRIVATE_CROP_INDEX = ROOT / "private/review-assets/issue19-p0-immediate-pdf-crops/crop-index.csv"
PRIVATE_FIELD_CONFIRM = (
    ROOT / "private/review-assets/issue19-p0-immediate-field-confirmation/field-confirmation-private-workbench.csv"
)

OUTPUT = ROOT / "data/working/issue19-p0-immediate-page-review-packets.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-p0-immediate-page-review-packets-summary.json"

PRIVATE_OUTPUT_DIR = ROOT / "private/review-assets/issue19-p0-immediate-page-review-packets"
PRIVATE_PACKET_INDEX = PRIVATE_OUTPUT_DIR / "page-side-packets-private-index.csv"
PRIVATE_HTML_DIR = PRIVATE_OUTPUT_DIR / "html"
PRIVATE_MASTER_HTML = PRIVATE_OUTPUT_DIR / "index.html"

SOURCE_ISSUE = "湖北招生考试2026年19期·本科普通批（下）"
SOURCE_PDF_SHA256 = "ee61fc69389f24a9a7830167113cf0ddc0447f8fa4b2743cd3241be60a9bd86d"
DATA_STAGE = "issue19_p0_immediate_page_review_packets"


FIELDS = [
    "P0即时按页核页包ID",
    "来源P0即时字段确认公开账本",
    "来源私有裁图索引",
    "来源私有字段确认工作台",
    "来源期号",
    "来源PDF_SHA256",
    "数据阶段",
    "主表粒度",
    "任务粒度",
    "最终可用",
    "可进入下一阶段",
    "机器是否允许自动写回主表",
    "机器是否允许自动回填候选",
    "是否允许写回字段",
    "是否允许作为志愿推荐依据",
    "是否允许生成学校专业建议",
    "按页核页包总序",
    "来源页码",
    "版面列",
    "页码版面键",
    "包内字段任务数",
    "包内专业行数",
    "包内裁图证据数",
    "包内字段名分布",
    "包内人工核验泳道分布",
    "包内执行批次分布",
    "包内裁图OCR辅助桶分布",
    "包内最高优先级数值",
    "包内是否含冲突优先任务",
    "包内是否含计划数偏大任务",
    "包内是否含裁图未稳定补读任务",
    "包内是否含高校辅证线索",
    "包内是否需要双人复核",
    "包内双人复核任务数",
    "包内高校辅证私有记录待完成数",
    "包内PDF私有记录待完成数",
    "包内湖北官方私有记录待完成数",
    "包内字段写回评估可进入数",
    "包内字段冲突阻断数",
    "字段确认公开账本ID集合",
    "P0字段即时复核任务ID集合",
    "裁图证据编号集合",
    "裁图文件SHA256集合",
    "裁图规格SHA256集合",
    "裁图bbox归一化集合",
    "私有页图证据编号集合",
    "私有页图SHA256集合",
    "私有审阅HTML证据编号",
    "私有审阅HTML_SHA256",
    "私有审阅任务CSV_SHA256",
    "私有审阅材料状态",
    "PDF原页核页状态",
    "湖北官方系统或省招办计划核验状态",
    "高校官网或招生章程辅证状态",
    "三方字段一致性状态",
    "字段事实写回状态",
    "公开安全策略",
    "下一步",
]

PRIVATE_FIELDS = FIELDS + [
    "私有审阅HTML相对路径",
    "私有审阅任务CSV相对路径",
    "私有裁图文件名集合",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def counter_text(counter):
    return "；".join(f"{key}:{value}" for key, value in sorted(counter.items())) if counter else ""


def join_unique(rows, field):
    values = []
    seen = set()
    for row in rows:
        value = row.get(field, "")
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return "；".join(values)


def packet_priority(rows):
    values = []
    for row in rows:
        try:
            values.append(int(row.get("人工核验优先级数值", "9999")))
        except ValueError:
            values.append(9999)
    return min(values) if values else 9999


def row_sort_key(row):
    try:
        priority = int(row.get("人工核验优先级数值", "9999"))
    except ValueError:
        priority = 9999
    try:
        order = int(row.get("字段确认公开账本总序", "9999"))
    except ValueError:
        order = 9999
    return priority, order, row.get("P0字段即时复核任务ID", "")


def private_html_for_packet(packet_id, rows, crop_by_task, private_by_public_id):
    page = rows[0].get("来源页码", "")
    side = rows[0].get("版面列", "")
    filename = f"{packet_id}.html"
    path = PRIVATE_HTML_DIR / filename
    lines = [
        "<!doctype html>",
        "<meta charset='utf-8'>",
        "<style>",
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:24px;line-height:1.45;color:#111}",
        ".task{border:1px solid #ccc;border-radius:8px;padding:12px;margin:14px 0;break-inside:avoid}",
        ".meta{font-size:13px;color:#444;margin:4px 0}",
        "img{max-width:100%;border:1px solid #ddd;background:white}",
        "table{border-collapse:collapse;width:100%;font-size:13px;margin-top:10px}",
        "td,th{border:1px solid #ddd;padding:6px;vertical-align:top}",
        ".warn{color:#9a3412;font-weight:600}",
        "</style>",
        f"<title>{html.escape(packet_id)} 第{html.escape(page)}页 {html.escape(side)}</title>",
        f"<h1>{html.escape(packet_id)} 第 {html.escape(page)} 页 {html.escape(side)}</h1>",
        "<p class='warn'>私有审阅材料：可显示本地裁图和候选线索，不得提交公开仓库。</p>",
    ]
    for row in rows:
        crop = crop_by_task.get(row.get("P0字段即时复核任务ID", ""), {})
        private_row = private_by_public_id.get(row.get("P0即时字段确认公开账本ID", ""), {})
        crop_file = crop.get("本地裁图文件名", "")
        rel_img = f"../../issue19-p0-immediate-pdf-crops/{crop_file}" if crop_file else ""
        lines.extend([
            "<section class='task'>",
            f"<h2>{html.escape(row.get('字段确认公开账本总序',''))}. {html.escape(row.get('字段名',''))} / {html.escape(row.get('人工核验泳道',''))}</h2>",
            f"<div class='meta'>专业行ID：{html.escape(row.get('专业行ID',''))}；任务ID：{html.escape(row.get('P0字段即时复核任务ID',''))}</div>",
            f"<div class='meta'>裁图证据：{html.escape(row.get('裁图证据编号',''))}；bbox：{html.escape(row.get('裁图bbox归一化',''))}</div>",
            f"<div class='meta'>动作：{html.escape(row.get('人工核验动作',''))}</div>",
        ])
        if rel_img:
            lines.append(f"<img src='{html.escape(rel_img)}' alt='{html.escape(row.get('裁图证据编号',''))}'>")
        lines.extend([
            "<table>",
            "<tr><th>线索类型</th><th>私有候选/记录</th></tr>",
            f"<tr><td>机器候选</td><td>{html.escape(private_row.get('机器候选字段值',''))} / {html.escape(private_row.get('机器候选规范值',''))}</td></tr>",
            f"<tr><td>高校辅证</td><td>{html.escape(private_row.get('高校官网字段候选值',''))} / {html.escape(private_row.get('高校官网字段规范值',''))}</td></tr>",
            f"<tr><td>裁图OCR</td><td>{html.escape(private_row.get('裁图OCR候选字段值',''))} / {html.escape(private_row.get('裁图OCR候选规范值',''))}<br>{html.escape(private_row.get('裁图OCR候选行文本',''))}</td></tr>",
            f"<tr><td>PDF原页</td><td>{html.escape(private_row.get('PDF原页人工读数',''))}</td></tr>",
            f"<tr><td>湖北官方</td><td>{html.escape(private_row.get('湖北官方字段值',''))}</td></tr>",
            f"<tr><td>高校或章程</td><td>{html.escape(private_row.get('高校官网或招生章程字段值',''))}</td></tr>",
            f"<tr><td>确认/备注</td><td>{html.escape(private_row.get('字段确认值',''))}<br>{html.escape(private_row.get('人工复核备注',''))}</td></tr>",
            "</table>",
            "</section>",
        ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def private_task_csv_for_packet(packet_id, rows, crop_by_task):
    path = PRIVATE_HTML_DIR / f"{packet_id}.csv"
    fields = [
        "P0即时字段确认公开账本ID",
        "P0字段即时复核任务ID",
        "来源页码",
        "版面列",
        "字段名",
        "专业行ID",
        "人工核验泳道",
        "人工核验方式",
        "裁图证据编号",
        "本地裁图文件名",
        "PDF原页人工读数",
        "湖北官方字段值",
        "高校官网或招生章程字段值",
        "字段确认值",
        "PDF核页复核人A",
        "PDF核页复核人B",
        "人工复核备注",
    ]
    out_rows = []
    for row in rows:
        crop = crop_by_task.get(row.get("P0字段即时复核任务ID", ""), {})
        out_rows.append({
            "P0即时字段确认公开账本ID": row.get("P0即时字段确认公开账本ID", ""),
            "P0字段即时复核任务ID": row.get("P0字段即时复核任务ID", ""),
            "来源页码": row.get("来源页码", ""),
            "版面列": row.get("版面列", ""),
            "字段名": row.get("字段名", ""),
            "专业行ID": row.get("专业行ID", ""),
            "人工核验泳道": row.get("人工核验泳道", ""),
            "人工核验方式": row.get("人工核验方式", ""),
            "裁图证据编号": row.get("裁图证据编号", ""),
            "本地裁图文件名": crop.get("本地裁图文件名", ""),
            "PDF原页人工读数": "",
            "湖北官方字段值": "",
            "高校官网或招生章程字段值": "",
            "字段确认值": "",
            "PDF核页复核人A": "",
            "PDF核页复核人B": "",
            "人工复核备注": "",
        })
    write_csv(path, out_rows, fields)
    return path


def build_master_html(private_rows):
    lines = [
        "<!doctype html>",
        "<meta charset='utf-8'>",
        "<title>P0 即时按页核页包</title>",
        "<h1>P0 即时按页核页包</h1>",
        "<p>私有索引：链接指向本地 HTML 审阅页，不得提交公开仓库。</p>",
        "<ol>",
    ]
    for row in private_rows:
        rel = Path(row["私有审阅HTML相对路径"]).name
        lines.append(
            f"<li><a href='html/{html.escape(rel)}'>{html.escape(row['P0即时按页核页包ID'])}</a> "
            f"第 {html.escape(row['来源页码'])} 页 {html.escape(row['版面列'])}，"
            f"{html.escape(row['包内字段任务数'])} 个任务，"
            f"{html.escape(row['包内人工核验泳道分布'])}</li>"
        )
    lines.append("</ol>")
    PRIVATE_MASTER_HTML.parent.mkdir(parents=True, exist_ok=True)
    PRIVATE_MASTER_HTML.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_rows():
    field_rows = read_csv(FIELD_CONFIRM_LEDGER)
    crop_by_task = {row["来源P0字段即时复核任务ID"]: row for row in read_csv(PRIVATE_CROP_INDEX)}
    private_by_public_id = {
        row["P0即时字段确认公开账本ID"]: row for row in read_csv(PRIVATE_FIELD_CONFIRM)
    }
    groups = defaultdict(list)
    for row in field_rows:
        groups[(int(row["来源页码"]), row["版面列"])].append(row)

    public_rows = []
    private_rows = []
    for index, ((page, side), rows) in enumerate(sorted(groups.items()), start=1):
        rows = sorted(rows, key=row_sort_key)
        packet_id = stable_id("P0PAGEPACK", [page, side, len(rows), rows[0]["P0字段即时复核任务ID"]])
        html_path = private_html_for_packet(packet_id, rows, crop_by_task, private_by_public_id)
        task_csv_path = private_task_csv_for_packet(packet_id, rows, crop_by_task)
        crop_rows = [crop_by_task[row["P0字段即时复核任务ID"]] for row in rows]
        field_counter = Counter(row["字段名"] for row in rows)
        lane_counter = Counter(row["人工核验泳道"] for row in rows)
        batch_counter = Counter(row["执行批次"] for row in rows)
        helper_counter = Counter(row["裁图OCR三方辅助桶"] for row in rows)
        double_count = sum(row["是否需要双人复核"] == "true" for row in rows)
        school_count = sum(row["高校辅证私有记录状态"] == "pending_private_school_reading" for row in rows)
        pdf_count = sum(row["PDF原页私有记录状态"] == "pending_private_pdf_reading" for row in rows)
        hubei_count = sum(row["湖北官方私有记录状态"] == "pending_private_hubei_reading" for row in rows)
        ready_count = sum(row["字段事实写回评估状态"] == "ready_for_manual_field_writeback_review" for row in rows)
        conflict_count = sum(row["字段事实写回评估状态"] == "blocked_conflict_needs_manual_resolution" for row in rows)
        public_row = {
            "P0即时按页核页包ID": packet_id,
            "来源P0即时字段确认公开账本": "data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv",
            "来源私有裁图索引": "private_crop_index_not_public",
            "来源私有字段确认工作台": "private_field_confirmation_workbench_not_public",
            "来源期号": SOURCE_ISSUE,
            "来源PDF_SHA256": SOURCE_PDF_SHA256,
            "数据阶段": DATA_STAGE,
            "主表粒度": "PDF页码×版面列",
            "任务粒度": "PDF页码×版面列×P0字段确认核页包",
            "最终可用": "false",
            "可进入下一阶段": "false",
            "机器是否允许自动写回主表": "false",
            "机器是否允许自动回填候选": "false",
            "是否允许写回字段": "false",
            "是否允许作为志愿推荐依据": "false",
            "是否允许生成学校专业建议": "false",
            "按页核页包总序": str(index),
            "来源页码": str(page),
            "版面列": side,
            "页码版面键": f"{page:03d}-{side}",
            "包内字段任务数": str(len(rows)),
            "包内专业行数": str(len({row["专业行ID"] for row in rows})),
            "包内裁图证据数": str(len({row["裁图证据编号"] for row in rows})),
            "包内字段名分布": counter_text(field_counter),
            "包内人工核验泳道分布": counter_text(lane_counter),
            "包内执行批次分布": counter_text(batch_counter),
            "包内裁图OCR辅助桶分布": counter_text(helper_counter),
            "包内最高优先级数值": str(packet_priority(rows)),
            "包内是否含冲突优先任务": "true" if any("冲突" in row["人工核验泳道"] for row in rows) else "false",
            "包内是否含计划数偏大任务": "true" if any("计划数偏大" in row["人工核验泳道"] for row in rows) else "false",
            "包内是否含裁图未稳定补读任务": "true" if any("未稳定补读" in row["人工核验泳道"] for row in rows) else "false",
            "包内是否含高校辅证线索": "true" if school_count else "false",
            "包内是否需要双人复核": "true" if double_count else "false",
            "包内双人复核任务数": str(double_count),
            "包内高校辅证私有记录待完成数": str(school_count),
            "包内PDF私有记录待完成数": str(pdf_count),
            "包内湖北官方私有记录待完成数": str(hubei_count),
            "包内字段写回评估可进入数": str(ready_count),
            "包内字段冲突阻断数": str(conflict_count),
            "字段确认公开账本ID集合": join_unique(rows, "P0即时字段确认公开账本ID"),
            "P0字段即时复核任务ID集合": join_unique(rows, "P0字段即时复核任务ID"),
            "裁图证据编号集合": join_unique(rows, "裁图证据编号"),
            "裁图文件SHA256集合": join_unique(rows, "裁图文件SHA256"),
            "裁图规格SHA256集合": join_unique(rows, "裁图规格SHA256"),
            "裁图bbox归一化集合": join_unique(rows, "裁图bbox归一化"),
            "私有页图证据编号集合": join_unique(crop_rows, "私有页图证据编号"),
            "私有页图SHA256集合": join_unique(crop_rows, "私有页图SHA256"),
            "私有审阅HTML证据编号": f"PRIVATEHTML-{packet_id}",
            "私有审阅HTML_SHA256": sha256(html_path),
            "私有审阅任务CSV_SHA256": sha256(task_csv_path),
            "私有审阅材料状态": "private_page_side_review_material_generated",
            "PDF原页核页状态": "pending_manual_pdf_review",
            "湖北官方系统或省招办计划核验状态": "pending_hubei_official_review",
            "高校官网或招生章程辅证状态": "pending_if_school_clue_present",
            "三方字段一致性状态": "pending_private_three_way_field_confirmation",
            "字段事实写回状态": "blocked_until_required_private_readings_complete",
            "公开安全策略": "公开表只保存按页核页包状态、任务ID、证据编号、SHA、bbox摘要和门禁；不保存本地HTML路径、裁图图片路径、字段记录值、候选值、识别文本、院校名、专业名、专业代号或专业组代码。",
            "下一步": "打开私有审阅HTML，按同一PDF页码和版面列逐条核PDF原页；完成私有字段确认工作台后再重新生成字段确认公开账本。",
        }
        private_row = {
            **public_row,
            "私有审阅HTML相对路径": str(html_path.relative_to(ROOT)),
            "私有审阅任务CSV相对路径": str(task_csv_path.relative_to(ROOT)),
            "私有裁图文件名集合": join_unique(crop_rows, "本地裁图文件名"),
        }
        public_rows.append(public_row)
        private_rows.append(private_row)

    build_master_html(private_rows)
    return public_rows, private_rows


def build_summary(public_rows):
    return {
        "status": "issue19_p0_immediate_page_review_packets_not_final",
        "generated_by": Path(__file__).name,
        "source_field_confirmation_public_ledger": "data/working/issue19-p0-immediate-field-confirmation-public-ledger.csv",
        "source_private_crop_index": "private_crop_index_not_public",
        "source_private_field_confirmation_workbench": "private_field_confirmation_workbench_not_public",
        "output_table": "data/working/issue19-p0-immediate-page-review-packets.csv",
        "row_grain": "PDF页码×版面列",
        "source_issue": SOURCE_ISSUE,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "row_count": len(public_rows),
        "private_page_side_review_material_generated": True,
        "unique_packet_id_count": len({row["P0即时按页核页包ID"] for row in public_rows}),
        "unique_pdf_page_count": len({row["来源页码"] for row in public_rows}),
        "unique_page_side_count": len({(row["来源页码"], row["版面列"]) for row in public_rows}),
        "total_field_task_count": sum(int(row["包内字段任务数"]) for row in public_rows),
        "total_crop_evidence_count": sum(int(row["包内裁图证据数"]) for row in public_rows),
        "total_double_review_task_count": sum(int(row["包内双人复核任务数"]) for row in public_rows),
        "total_school_private_record_pending_count": sum(int(row["包内高校辅证私有记录待完成数"]) for row in public_rows),
        "total_pdf_private_record_pending_count": sum(int(row["包内PDF私有记录待完成数"]) for row in public_rows),
        "total_hubei_private_record_pending_count": sum(int(row["包内湖北官方私有记录待完成数"]) for row in public_rows),
        "total_field_writeback_ready_count": sum(int(row["包内字段写回评估可进入数"]) for row in public_rows),
        "total_field_conflict_blocked_count": sum(int(row["包内字段冲突阻断数"]) for row in public_rows),
        "packet_task_count_distribution": dict(Counter(row["包内字段任务数"] for row in public_rows)),
        "page_side_counts": dict(Counter(row["版面列"] for row in public_rows)),
        "packets_with_conflict_priority_count": sum(row["包内是否含冲突优先任务"] == "true" for row in public_rows),
        "packets_with_large_plan_count": sum(row["包内是否含计划数偏大任务"] == "true" for row in public_rows),
        "packets_with_unstable_crop_ocr_count": sum(row["包内是否含裁图未稳定补读任务"] == "true" for row in public_rows),
        "packets_with_school_clue_count": sum(row["包内是否含高校辅证线索"] == "true" for row in public_rows),
        "packets_requiring_double_review_count": sum(row["包内是否需要双人复核"] == "true" for row in public_rows),
        "final_available_count": sum(row["最终可用"] == "true" for row in public_rows),
        "next_stage_available_count": sum(row["可进入下一阶段"] == "true" for row in public_rows),
        "field_writeback_allowed_count": sum(row["是否允许写回字段"] == "true" for row in public_rows),
        "recommendation_basis_allowed_count": sum(row["是否允许作为志愿推荐依据"] == "true" for row in public_rows),
        "school_major_suggestion_allowed_count": sum(row["是否允许生成学校专业建议"] == "true" for row in public_rows),
        "public_safety_note": "公开按页核页包只保存任务ID、证据编号、SHA、bbox摘要和门禁；不保存本地HTML路径、裁图图片路径、字段记录值、候选值或识别文本。",
    }


def main():
    public_rows, private_rows = build_rows()
    write_csv(OUTPUT, public_rows, FIELDS)
    write_csv(PRIVATE_PACKET_INDEX, private_rows, PRIVATE_FIELDS)
    write_json(SUMMARY_OUTPUT, build_summary(public_rows))
    print(f"写出 {OUTPUT.relative_to(ROOT)}：{len(public_rows)} 行")
    print(f"写出 {PRIVATE_PACKET_INDEX.relative_to(ROOT)}：{len(private_rows)} 行")
    print(f"写出 {PRIVATE_MASTER_HTML.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
