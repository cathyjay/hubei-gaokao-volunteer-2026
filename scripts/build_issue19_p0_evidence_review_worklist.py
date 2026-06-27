#!/usr/bin/env python3
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
P0_PACKETS = ROOT / "data/working/issue19-p0-evidence-execution-packets.csv"
FULL_EVIDENCE = ROOT / "data/working/issue19-full-major-evidence-workbench.csv"
PAGE_MANIFEST = ROOT / "data/working/issue19-page-manifest.csv"
PAGE_FIDELITY = ROOT / "data/working/issue19-page-fidelity-review-queue.csv"
OUTPUT = ROOT / "data/working/issue19-p0-evidence-review-worklist.csv"
SUMMARY_OUTPUT = ROOT / "data/working/issue19-p0-evidence-review-worklist-summary.json"

DATA_STAGE = "issue19_p0_evidence_review_worklist"


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stable_id(prefix, parts):
    text = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def as_int(value):
    try:
        return int(str(value or "").strip())
    except ValueError:
        return 0


def main():
    p0_rows = read_csv(P0_PACKETS)
    full_rows = read_csv(FULL_EVIDENCE)
    manifest_rows = read_csv(PAGE_MANIFEST)
    page_fidelity_rows = read_csv(PAGE_FIDELITY)

    full_by_id = {row.get("全量证据工作台ID"): row for row in full_rows}
    manifest_by_page = {row.get("PDF页码"): row for row in manifest_rows}
    page_fidelity_by_page = {row.get("PDF页码"): row for row in page_fidelity_rows}

    packet_type_order = {
        "P0A-PDF原页结构阻断": 1,
        "P0B-三方证据闭环": 2,
        "P0C-B0B1差异复核": 3,
    }
    evidence_item_order = {
        "PDF原页核验": 1,
        "湖北官方系统/省招办计划核验": 2,
        "高校官网/章程辅证": 3,
        "B0/B1官网冲突或未匹配复核": 4,
    }

    output_rows = []
    full_hit_count = 0
    manifest_hit_count = 0
    page_fidelity_hit_count = 0
    for row in sorted(
        p0_rows,
        key=lambda item: (
            as_int(item.get("P0页码优先序")),
            as_int(item.get("P0学校优先序")),
            packet_type_order.get(item.get("P0执行包类型"), 99),
            as_int(item.get("专业组内专业序号")),
            evidence_item_order.get(item.get("证据项"), 99),
            item.get("P0执行包任务ID", ""),
        ),
    ):
        full_row = full_by_id.get(row.get("来源全量证据工作台ID"), {})
        manifest_row = manifest_by_page.get(row.get("来源页码"), {})
        page_row = page_fidelity_by_page.get(row.get("来源页码"), {})
        full_hit_count += bool(full_row)
        manifest_hit_count += bool(manifest_row)
        page_fidelity_hit_count += bool(page_row)

        output_rows.append({
            "P0复核工作清单ID": stable_id(
                "P0REVIEW",
                [row.get("P0执行包任务ID", ""), row.get("来源全量证据工作台ID", "")],
            ),
            "来源P0执行包表": "data/working/issue19-p0-evidence-execution-packets.csv",
            "来源P0执行包任务ID": row.get("P0执行包任务ID", ""),
            "来源P0执行包ID": row.get("P0执行包ID", ""),
            "来源证据闭环任务ID": row.get("来源证据闭环任务ID", ""),
            "来源全量证据工作台ID": row.get("来源全量证据工作台ID", ""),
            "来源全量证据工作台": "data/working/issue19-full-major-evidence-workbench.csv",
            "来源页级manifest": "data/working/issue19-page-manifest.csv",
            "来源页级保真复核队列": "data/working/issue19-page-fidelity-review-queue.csv",
            "来源期号": full_row.get("来源期号", ""),
            "来源PDF_SHA256": full_row.get("来源PDF_SHA256", ""),
            "数据阶段": DATA_STAGE,
            "主表粒度": "逐专业招生明细",
            "任务粒度": "逐专业招生明细×P0证据项",
            "最终可用": "false",
            "是否可升级": "false",
            "是否可进入最终专业列表": "false",
            "可进入下一阶段": "false",
            "P0复核结论状态": "pending_p0_manual_review",
            "P0执行包类型": row.get("P0执行包类型", ""),
            "P0页码优先序": row.get("P0页码优先序", ""),
            "P0学校优先序": row.get("P0学校优先序", ""),
            "P0页内任务数": row.get("P0页内任务数", ""),
            "P0学校任务数": row.get("P0学校任务数", ""),
            "证据项": row.get("证据项", ""),
            "证据任务优先级": row.get("证据任务优先级", ""),
            "证据任务状态": row.get("证据任务状态", ""),
            "需要核验字段": row.get("需要核验字段", ""),
            "执行动作代码": row.get("执行动作代码", ""),
            "阻断或待核原因": row.get("阻断或待核原因", ""),
            "PDF页码": row.get("来源页码", ""),
            "私有页图证据编号": manifest_row.get("私有页图证据编号", ""),
            "私有页图SHA256": manifest_row.get("私有页图SHA256", ""),
            "私有OCR文本证据编号": manifest_row.get("私有OCR文本证据编号", ""),
            "私有OCR文本SHA256": manifest_row.get("私有OCR文本SHA256", ""),
            "OCR平均置信度": manifest_row.get("OCR平均置信度", ""),
            "OCR_QC_P0数": manifest_row.get("OCR_QC_P0数", ""),
            "OCR_QC_P1数": manifest_row.get("OCR_QC_P1数", ""),
            "页面复核优先级": page_row.get("页面复核优先级", ""),
            "页面阻断等级": page_row.get("页面阻断等级", ""),
            "页面专业明细数": page_row.get("页面专业明细数", ""),
            "页面结构异常数": page_row.get("页面结构异常数", ""),
            "页面高严重结构异常数": page_row.get("页面高严重结构异常数", ""),
            "风险字段Top": page_row.get("风险字段Top", ""),
            "风险规则Top": page_row.get("风险规则Top", ""),
            "专业行ID": row.get("专业行ID", ""),
            "专业组出现ID": row.get("专业组出现ID", ""),
            "院校代码": row.get("院校代码", ""),
            "院校名称OCR": row.get("院校名称OCR", ""),
            "院校专业组代码OCR规范化": row.get("院校专业组代码OCR规范化", ""),
            "版面列": full_row.get("版面列", ""),
            "专业组内专业序号": row.get("专业组内专业序号", ""),
            "专业代号OCR": row.get("专业代号OCR", ""),
            "专业名称及备注OCR": full_row.get("专业名称及备注OCR", row.get("专业名称及备注OCR短摘", "")),
            "再选科目OCR候选": full_row.get("再选科目OCR候选", ""),
            "专业计划数OCR候选": full_row.get("专业计划数OCR候选", ""),
            "学费OCR候选": full_row.get("学费OCR候选", ""),
            "专业偏好方向": full_row.get("专业偏好方向", ""),
            "专业风险类型": full_row.get("专业风险类型", ""),
            "机器专业接受度初判": full_row.get("机器专业接受度初判", ""),
            "机器阻断或待核原因": full_row.get("机器阻断或待核原因", ""),
            "同组真实招生明细数": full_row.get("同组真实招生明细数", ""),
            "同组偏好专业数": full_row.get("同组偏好专业数", ""),
            "同组医学护理排除专业数": full_row.get("同组医学护理排除专业数", ""),
            "同组高收费或超预算专业数": full_row.get("同组高收费或超预算专业数", ""),
            "同组特殊限制待核专业数": full_row.get("同组特殊限制待核专业数", ""),
            "调剂影响等级": full_row.get("调剂影响等级", ""),
            "组机器家庭匹配初判": full_row.get("组机器家庭匹配初判", ""),
            "组调剂初判": full_row.get("组调剂初判", ""),
            "三年投档线索": full_row.get("三年投档线索", ""),
            "三年投档稳定性状态": full_row.get("三年投档稳定性状态", ""),
            "高校官网/章程辅证状态": full_row.get("高校官网/章程辅证状态", ""),
            "高校官网URL": full_row.get("高校官网URL", ""),
            "高校官网可核字段": full_row.get("高校官网可核字段", ""),
            "高校官网局限性": full_row.get("高校官网局限性", ""),
            "B0B1计划冲突来源明细ID": full_row.get("B0B1计划冲突来源明细ID", ""),
            "B0B1未匹配专业来源明细ID": full_row.get("B0B1未匹配专业来源明细ID", ""),
            "计划数核验状态": full_row.get("计划数核验状态", ""),
            "执行必须核验字段": full_row.get("执行必须核验字段", ""),
            "证据缺口": full_row.get("证据缺口", ""),
            "PDF原页人工核验结论状态": "pending_original_pdf_page_review",
            "湖北官方系统证据状态": full_row.get("湖北官方系统证据状态", ""),
            "湖北官方系统人工核验结论状态": "pending_hubei_official_plan_review",
            "高校官网/章程人工核验结论状态": "pending_school_plan_or_charter_review",
            "家庭接受度人工结论状态": "pending_family_acceptance_review",
            "同组调剂人工结论状态": "pending_transfer_decision",
            "湖北官方系统证据编号": "",
            "湖北官方系统证据SHA256": "",
            "高校官网/章程证据编号": "",
            "高校官网/章程证据SHA256": "",
            "人工核验人": "",
            "人工核验时间": "",
            "人工核验备注": "",
            "下一步": (
                "按本行证据项执行；先回看PDF原页和页图证据编号，再核湖北官方系统/省招办计划、"
                "高校官网/章程、家庭接受度、同组调剂和三年投档稳定性。不得只按P0执行包ID作最终结论。"
            ),
        })

    fields = [
        "P0复核工作清单ID",
        "来源P0执行包表",
        "来源P0执行包任务ID",
        "来源P0执行包ID",
        "来源证据闭环任务ID",
        "来源全量证据工作台ID",
        "来源全量证据工作台",
        "来源页级manifest",
        "来源页级保真复核队列",
        "来源期号",
        "来源PDF_SHA256",
        "数据阶段",
        "主表粒度",
        "任务粒度",
        "最终可用",
        "是否可升级",
        "是否可进入最终专业列表",
        "可进入下一阶段",
        "P0复核结论状态",
        "P0执行包类型",
        "P0页码优先序",
        "P0学校优先序",
        "P0页内任务数",
        "P0学校任务数",
        "证据项",
        "证据任务优先级",
        "证据任务状态",
        "需要核验字段",
        "执行动作代码",
        "阻断或待核原因",
        "PDF页码",
        "私有页图证据编号",
        "私有页图SHA256",
        "私有OCR文本证据编号",
        "私有OCR文本SHA256",
        "OCR平均置信度",
        "OCR_QC_P0数",
        "OCR_QC_P1数",
        "页面复核优先级",
        "页面阻断等级",
        "页面专业明细数",
        "页面结构异常数",
        "页面高严重结构异常数",
        "风险字段Top",
        "风险规则Top",
        "专业行ID",
        "专业组出现ID",
        "院校代码",
        "院校名称OCR",
        "院校专业组代码OCR规范化",
        "版面列",
        "专业组内专业序号",
        "专业代号OCR",
        "专业名称及备注OCR",
        "再选科目OCR候选",
        "专业计划数OCR候选",
        "学费OCR候选",
        "专业偏好方向",
        "专业风险类型",
        "机器专业接受度初判",
        "机器阻断或待核原因",
        "同组真实招生明细数",
        "同组偏好专业数",
        "同组医学护理排除专业数",
        "同组高收费或超预算专业数",
        "同组特殊限制待核专业数",
        "调剂影响等级",
        "组机器家庭匹配初判",
        "组调剂初判",
        "三年投档线索",
        "三年投档稳定性状态",
        "高校官网/章程辅证状态",
        "高校官网URL",
        "高校官网可核字段",
        "高校官网局限性",
        "B0B1计划冲突来源明细ID",
        "B0B1未匹配专业来源明细ID",
        "计划数核验状态",
        "执行必须核验字段",
        "证据缺口",
        "PDF原页人工核验结论状态",
        "湖北官方系统证据状态",
        "湖北官方系统人工核验结论状态",
        "高校官网/章程人工核验结论状态",
        "家庭接受度人工结论状态",
        "同组调剂人工结论状态",
        "湖北官方系统证据编号",
        "湖北官方系统证据SHA256",
        "高校官网/章程证据编号",
        "高校官网/章程证据SHA256",
        "人工核验人",
        "人工核验时间",
        "人工核验备注",
        "下一步",
    ]
    write_csv(OUTPUT, output_rows, fields)

    summary = {
        "status": "issue19_p0_evidence_review_worklist_not_final",
        "generated_by": "build_issue19_p0_evidence_review_worklist.py",
        "source_p0_execution_packets": "data/working/issue19-p0-evidence-execution-packets.csv",
        "source_full_major_evidence_workbench": "data/working/issue19-full-major-evidence-workbench.csv",
        "source_page_manifest": "data/working/issue19-page-manifest.csv",
        "source_page_fidelity_review_queue": "data/working/issue19-page-fidelity-review-queue.csv",
        "output_table": "data/working/issue19-p0-evidence-review-worklist.csv",
        "source_p0_task_row_count": len(p0_rows),
        "worklist_row_count": len(output_rows),
        "unique_worklist_id_count": len({row["P0复核工作清单ID"] for row in output_rows}),
        "unique_source_p0_task_id_count": len({row["来源P0执行包任务ID"] for row in output_rows}),
        "unique_source_closure_task_id_count": len({row["来源证据闭环任务ID"] for row in output_rows}),
        "unique_major_line_id_count": len({row["专业行ID"] for row in output_rows}),
        "unique_packet_id_count": len({row["来源P0执行包ID"] for row in output_rows}),
        "unique_pdf_page_count": len({row["PDF页码"] for row in output_rows}),
        "unique_school_count": len({row["院校代码"] for row in output_rows}),
        "full_evidence_hit_count": full_hit_count,
        "page_manifest_hit_count": manifest_hit_count,
        "page_fidelity_hit_count": page_fidelity_hit_count,
        "final_available_count": sum(row["最终可用"] == "true" for row in output_rows),
        "auto_upgrade_allowed_count": sum(row["是否可升级"] == "true" for row in output_rows),
        "next_stage_allowed_count": sum(row["可进入下一阶段"] == "true" for row in output_rows),
        "final_major_list_candidate_count": sum(row["是否可进入最终专业列表"] == "true" for row in output_rows),
        "packet_type_counts": dict(Counter(row["P0执行包类型"] for row in output_rows)),
        "evidence_item_counts": dict(Counter(row["证据项"] for row in output_rows)),
        "task_status_counts": dict(Counter(row["证据任务状态"] for row in output_rows)),
        "school_source_status_counts": dict(Counter(row["高校官网/章程辅证状态"] for row in output_rows)),
        "manual_gate_status_counts": {
            "P0复核结论状态": dict(Counter(row["P0复核结论状态"] for row in output_rows)),
            "PDF原页人工核验结论状态": dict(Counter(row["PDF原页人工核验结论状态"] for row in output_rows)),
            "湖北官方系统人工核验结论状态": dict(Counter(row["湖北官方系统人工核验结论状态"] for row in output_rows)),
            "高校官网/章程人工核验结论状态": dict(Counter(row["高校官网/章程人工核验结论状态"] for row in output_rows)),
            "家庭接受度人工结论状态": dict(Counter(row["家庭接受度人工结论状态"] for row in output_rows)),
            "同组调剂人工结论状态": dict(Counter(row["同组调剂人工结论状态"] for row in output_rows)),
        },
        "notes": [
            "本表仍是一行一个招生专业明细和一个P0证据项。",
            "页图/OCR文本只公开证据编号和SHA，不公开私有路径、图片或整页OCR文本。",
            "所有人工证据编号和结论字段默认空或pending，不能据此进入最终志愿排序。",
        ],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
