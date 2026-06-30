#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软著前置采集表生成器
生成包含8组字段的结构化采集表 Markdown 和 JSON 字段契约。
用法: python generate_input_form.py [--output-dir <输出目录>]
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


FIELDS = {
    "registration": {
        "title": "一、登记与权属",
        "description": "请填写软件著作权的基本登记信息。",
        "fields": [
            {"id": "software_full_name", "label": "软件全称", "required": True,
             "placeholder": "如：演示任务管理系统", "hint": "与后续所有文档中的名称保持一致"},
            {"id": "software_short_name", "label": "软件简称", "required": False,
             "placeholder": "如：任务管理（无可留空）", "hint": "可选"},
            {"id": "version", "label": "版本号", "required": True,
             "placeholder": "如：V1.0", "hint": "如首次申报建议 V1.0"},
            {"id": "copyright_owner", "label": "著作权人", "required": True,
             "placeholder": "填写申请主体全称", "hint": "公司名称或个人信息"},
            {"id": "copyright_owner_type", "label": "著作权人类型", "required": False,
             "placeholder": "企业 / 个人 / 事业单位 / 其他", "hint": "不确定写\"待确认\""},
            {"id": "contact_person", "label": "申请联系人", "required": False,
             "placeholder": "姓名或对接人", "hint": "仅用于本次沟通"},
            {"id": "right_acquisition", "label": "权利取得方式", "required": False,
             "placeholder": "原始取得 / 继受取得", "hint": "自己开发的选\"原始取得\""},
            {"id": "right_scope", "label": "权利范围", "required": False,
             "placeholder": "全部权利 / 部分权利", "hint": "不确定写\"待确认\""},
            {"id": "development_method", "label": "开发方式", "required": False,
             "placeholder": "独立开发 / 合作开发 / 委托开发 / 下达任务开发",
             "hint": "单人/单公司开发选\"独立开发\""},
            {"id": "rights_note", "label": "权属补充说明", "required": False,
             "placeholder": "如有权属协议或特殊情况请在此说明", "hint": "一般无特殊情况可留空"},
        ]
    },
    "development": {
        "title": "二、开发与发表",
        "description": "请填写软件开发及发表相关信息。",
        "fields": [
            {"id": "completion_date", "label": "开发完成日期", "required": True,
             "placeholder": "YYYY-MM-DD（如 2025-06-01）", "hint": "可写\"留空\"（软著允许留空）"},
            {"id": "publication_status", "label": "发表状态", "required": True,
             "placeholder": "未发表 / 已发表", "hint": "上线/发布即视为已发表"},
            {"id": "first_publication_date", "label": "首次发表日期", "required": False,
             "placeholder": "YYYY-MM-DD", "hint": "已发表时填写，可写\"留空\""},
            {"id": "first_publication_city", "label": "首次发表城市", "required": False,
             "placeholder": "如：北京", "hint": "已发表时填"},
            {"id": "software_category", "label": "软件分类", "required": False,
             "placeholder": "应用软件 / 系统软件 / 支撑软件 / 嵌入式软件 / 其他",
             "hint": "一般Web/App/桌面程序选\"应用软件\""},
            {"id": "hardware_env", "label": "硬件环境", "required": True,
             "placeholder": "如：通用PC（CPU Intel i5及以上、内存8GB及以上、硬盘256GB及以上）",
             "hint": "描述最低硬件要求"},
            {"id": "os_env", "label": "操作系统", "required": True,
             "placeholder": "如：Windows 10、macOS 12、Android 10、iOS 15、Linux",
             "hint": "运行本软件所需的操作系统"},
            {"id": "runtime_env", "label": "运行支撑环境", "required": False,
             "placeholder": "如：JDK 17、Node.js 18、Python 3.10、MySQL 8.0",
             "hint": "运行所需的中间件/解释器/数据库"},
            {"id": "dev_tools", "label": "开发工具", "required": False,
             "placeholder": "如：VS Code、IntelliJ IDEA、Android Studio",
             "hint": "开发本软件使用的IDE和工具"},
            {"id": "programming_language", "label": "编程语言", "required": True,
             "placeholder": "如：Java、Python、JavaScript/TypeScript、Go",
             "hint": "源代码主体使用的语言"},
            {"id": "version_note", "label": "版本说明", "required": False,
             "placeholder": "如：首次申报 / 升级版本V2.0 / 补充登记",
             "hint": "首次申报可以留空"},
        ]
    },
    "project": {
        "title": "三、项目形态与仓库",
        "description": "请填写项目的代码仓库和目录结构信息。",
        "fields": [
            {"id": "repo_mode", "label": "仓库模式", "required": True,
             "placeholder": "单体仓库 / 前后分离 / 多仓库 / 其他",
             "hint": "前后端在同一个目录选\"单体仓库\"，分开部署选\"前后分离\""},
            {"id": "project_root", "label": "项目根目录", "required": True,
             "placeholder": "如：D:/my-project 或 /home/user/project",
             "hint": "单体仓库直接填根目录；前后分离填最上层的父目录"},
            {"id": "frontend_path", "label": "前端代码位置", "required": False,
             "placeholder": "如：项目根目录下的 frontend/ 或 web/",
             "hint": "前后分离或多仓库时填写，相对或绝对路径"},
            {"id": "backend_path", "label": "后端代码位置", "required": False,
             "placeholder": "如：项目根目录下的 backend/ 或 server/",
             "hint": "前后分离或多仓库时填写"},
            {"id": "mobile_path", "label": "移动端代码位置", "required": False,
             "placeholder": "如：android/ 或 ios/",
             "hint": "存在移动端时填写"},
            {"id": "exclude_dirs", "label": "需排除的目录", "required": False,
             "placeholder": "如：node_modules, dist, .git, vendor, target, build, __pycache__",
             "hint": "这些目录会被自动排除，有额外的可以补充"},
        ]
    },
    "business": {
        "title": "四、业务范围与用户手册",
        "description": "请描述软件的业务范围和目标用户。",
        "fields": [
            {"id": "business_domain", "label": "业务领域", "required": False,
             "placeholder": "如：办公协同、电商零售、医疗健康、生产管理、教育学习",
             "hint": "帮助确定手册描述风格"},
            {"id": "target_users", "label": "目标用户", "required": False,
             "placeholder": "如：企业管理员、一线业务人员、个人用户",
             "hint": "主要使用本软件的群体"},
            {"id": "covered_modules", "label": "申报覆盖的功能模块", "required": True,
             "placeholder": "如：用户登录、任务管理、数据报表、系统设置（每行一个）",
             "hint": "本次软著申报中要写入手册的功能"},
            {"id": "excluded_modules", "label": "不纳入的功能模块", "required": False,
             "placeholder": "如：支付模块（由第三方提供）、管理后台",
             "hint": "避免超范围材料"},
            {"id": "core_workflow", "label": "核心操作流程", "required": False,
             "placeholder": "如：登录 → 创建工单 → 审批 → 执行 → 关闭",
             "hint": "用箭头串联主要操作步骤"},
            {"id": "manual_chapter_style", "label": "手册章节组织方式", "required": False,
             "placeholder": "按菜单组织 / 按角色组织 / 按流程组织",
             "hint": "建议\"按菜单组织\"，与用户界面一致"},
            {"id": "glossary", "label": "专有名词或术语", "required": False,
             "placeholder": "如：工单（WorkOrder）— 记录任务和处理的实体",
             "hint": "用于术语表统一表述"},
        ]
    },
    "source_code": {
        "title": "五、源码材料",
        "description": "请确认源代码材料的生成策略。",
        "fields": [
            {"id": "source_strategy", "label": "源码抽取策略", "required": True,
             "placeholder": "自动建议 / 用户指定文件清单",
             "hint": "\"自动建议\"由 AI 分析项目后推荐抽取文件"},
            {"id": "priority_modules", "label": "优先纳入的模块", "required": False,
             "placeholder": "如：src/pages/、src/controllers/、src/services/",
             "hint": "AI 自动建议时可补充优先路径"},
            {"id": "source_order", "label": "源码排列顺序", "required": False,
             "placeholder": "前端在前 / 后端在前 / 按模块排列 / 按文件路径排列",
             "hint": "前后端都有时建议\"前端在前\""},
            {"id": "lines_per_page", "label": "每页行数", "required": True,
             "placeholder": "50（默认）", "hint": "通常 50~60 行/页"},
            {"id": "page_rule", "label": "页数口径", "required": True,
             "placeholder": "前30页+后30页（默认）",
             "hint": "超过60页取前30后30，不足60页全交"},
        ]
    },
    "screenshot": {
        "title": "六、运行与截图",
        "description": "请确认用户手册中的截图处理方式。",
        "fields": [
            {"id": "screenshot_method", "label": "截图方式", "required": True,
             "placeholder": "用户提供 / 暂不截图",
             "hint": "\"用户提供\"：您自己截图后提供；\"暂不截图\"：手册中留空白占位"},
            {"id": "screenshots_needed", "label": "需要截图的页面", "required": False,
             "placeholder": "如：登录页、首页、任务列表页、工单详情页、报表页",
             "hint": "列出需要截图的核心页面，每行一个"},
            {"id": "screenshot_dir", "label": "用户截图存放目录", "required": False,
             "placeholder": "如：D:/screenshots/",
             "hint": "选择\"用户提供\"时填写"},
        ]
    },
    "template_output": {
        "title": "七、模板与输出",
        "description": "请确认输出格式和目录。",
        "fields": [
            {"id": "output_dir", "label": "输出目录", "required": True,
             "placeholder": "软著申请资料（默认）",
             "hint": "在当前工作目录下创建，可自定义子目录名"},
            {"id": "output_format", "label": "输出格式", "required": True,
             "placeholder": "PDF / Markdown / DOCX",
             "hint": "建议 PDF；DOCX 可后续手动编辑"},
            {"id": "has_template", "label": "是否有历史申请表模板", "required": False,
             "placeholder": "是(提供路径) / 否",
             "hint": "有历史 Word 模板可以套打，不需要重新生成"},
            {"id": "other_notes", "label": "其他说明", "required": False,
             "placeholder": "特殊边界条件或要求",
             "hint": "一般留空"},
        ]
    },
    "review": {
        "title": "八、正式资料检查",
        "description": "请指定最终资料中不应出现的词汇和不一致检查点。",
        "fields": [
            {"id": "forbidden_words", "label": "不应出现的禁用词", "required": False,
             "placeholder": "如：旧系统名、内部代号、临时项目名（每行一个）",
             "hint": "生成后会自动检查并报告"},
            {"id": "consistency_focus", "label": "一致检查重点", "required": False,
             "placeholder": "如：软件全称、版本号、著作权人名称",
             "hint": "一般不需要额外指定"},
        ]
    }
}


def generate_markdown_form(output_dir: Path) -> str:
    """生成 Markdown 格式的前置采集表"""
    lines = []
    lines.append("# 软著申请前置采集表")
    lines.append("")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("> 请在各字段后的 `【请用户输入】` 处填写，填完后发回给我继续。")
    lines.append("")
    lines.append("---")
    lines.append("")

    for section_key, section in FIELDS.items():
        lines.append(f"## {section['title']}")
        lines.append("")
        if section.get("description"):
            lines.append(f"> {section['description']}")
            lines.append("")

        for field in section["fields"]:
            req_mark = " [OK]必填" if field["required"] else ""
            lines.append(f"### {field['label']}{req_mark}")
            lines.append("")
            lines.append(f"`【请用户输入】`")
            lines.append("")
            lines.append(f"> [TIP] {field['hint']}")
            lines.append(f"> [NOTE] 占位示例：{field['placeholder']}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def generate_json_contract(output_dir: Path) -> dict:
    """生成 JSON 字段契约"""
    contract = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "sections": {}
    }
    for section_key, section in FIELDS.items():
        contract["sections"][section_key] = {
            "title": section["title"],
            "description": section.get("description", ""),
            "fields": []
        }
        for field in section["fields"]:
            contract["sections"][section_key]["fields"].append({
                "id": field["id"],
                "label": field["label"],
                "required": field["required"],
                "placeholder": field["placeholder"],
                "hint": field["hint"]
            })
    return contract


def main():
    import argparse

    parser = argparse.ArgumentParser(description="生成软著前置采集表")
    parser.add_argument("--output-dir", default="软著申请资料",
                        help="输出目录 (默认: 软著申请资料)")
    parser.add_argument("--format", choices=["markdown", "json", "both"],
                        default="both", help="输出格式 (默认: both)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.format in ("markdown", "both"):
        md_path = output_dir / "前置采集表.md"
        md_content = generate_markdown_form(output_dir)
        md_path.write_text(md_content, encoding="utf-8")
        print(f"[OK] Markdown 采集表已生成: {md_path}")
        print()
        print(md_content)

    if args.format in ("json", "both"):
        json_path = output_dir / "前置采集字段.json"
        contract = generate_json_contract(output_dir)
        json_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        print(f"\n[OK] JSON 字段契约已生成: {json_path}")

    print("\n[*] 表单共包含 8 组字段，约 50+ 项。请逐项填写后回复给我。")


if __name__ == "__main__":
    main()
