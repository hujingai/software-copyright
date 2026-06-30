#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户手册草稿生成器
根据采集信息和业务理解生成结构化的用户使用说明书 Markdown 草稿。
用法: python generate_manual_draft.py --info <采集信息JSON> [--business <业务理解JSON>] [--out <输出目录>]
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def load_info(info_path: str) -> dict:
    """加载采集信息"""
    with open(info_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_cover_section(info: dict) -> str:
    """生成封面部分"""
    lines = []
    lines.append(f"# {info.get('software_full_name', '未命名软件')}")
    lines.append("")
    lines.append("## 用户使用说明书")
    lines.append("")
    lines.append("| 项目 | 内容 |")
    lines.append("|------|------|")
    lines.append(f"| 软件名称 | {info.get('software_full_name', '')} |")
    lines.append(f"| 版本号 | {info.get('version', '')} |")
    lines.append(f"| 著作权人 | {info.get('copyright_owner', '')} |")
    lines.append(f"| 编制日期 | {datetime.now().strftime('%Y年%m月%d日')} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def generate_disclaimer_section(info: dict) -> str:
    """生成声明部分"""
    lines = []
    lines.append("## 声明")
    lines.append("")
    lines.append("本手册中提及的软件产品相关权利归著作权人所有。")
    lines.append("未经著作权人书面授权，任何个人或组织不得擅自复制、传播、修改本手册或软件。")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def generate_intro_section(info: dict, business: Optional[dict] = None) -> str:
    """生成引言部分"""
    sw_name = info.get('software_full_name', '本软件')
    domain = info.get('business_domain', '通用')
    target = info.get('target_users', '所有用户')

    lines = []
    lines.append("## 一、引言")
    lines.append("")

    # 1.1 软件概述
    lines.append("### 1.1 软件概述")
    lines.append("")
    overview = info.get('software_overview', '')
    if not overview:
        overview = f"{sw_name}是一款面向{target}的{domain}类应用软件，旨在帮助用户高效完成相关工作。"
    lines.append(overview)
    lines.append("")

    # 1.2 适用对象
    lines.append("### 1.2 适用对象")
    lines.append("")
    lines.append(f"本手册适用于{sw_name}的{target}。")
    lines.append("")

    # 1.3 术语表
    glossary_text = info.get('glossary', '')
    if glossary_text:
        lines.append("### 1.3 术语说明")
        lines.append("")
        for term in glossary_text.strip().split('\n'):
            term = term.strip()
            if term:
                lines.append(f"- {term}")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def generate_requirements_section(info: dict) -> str:
    """生成系统要求部分"""
    lines = []
    lines.append("## 二、系统要求")
    lines.append("")

    lines.append("### 2.1 硬件环境")
    lines.append("")
    hardware = info.get('hardware_env', '通用个人计算机（CPU 2.0GHz及以上、内存 4GB及以上、硬盘 50GB及以上）')
    lines.append(hardware)
    lines.append("")

    lines.append("### 2.2 操作系统")
    lines.append("")
    os_env = info.get('os_env', 'Windows 10 及以上版本')
    lines.append(os_env)
    lines.append("")

    runtime = info.get('runtime_env', '')
    if runtime:
        lines.append("### 2.3 运行支撑环境")
        lines.append("")
        lines.append(runtime)
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def generate_install_section(info: dict) -> str:
    """生成安装说明部分"""
    lines = []
    lines.append("## 三、安装与启动")
    lines.append("")

    lines.append("### 3.1 安装步骤")
    lines.append("")
    lines.append(f"1. 获取 {info.get('software_full_name', '本软件')} 安装包")
    lines.append("2. 按照安装向导提示完成安装")
    runtime = info.get('runtime_env', '')
    if runtime:
        lines.append(f"3. 确认已安装必要的运行环境：{runtime}")
    lines.append("")

    lines.append("### 3.2 启动软件")
    lines.append("")
    lines.append(f"安装完成后，通过以下方式启动 {info.get('software_full_name', '本软件')}：")
    lines.append("")
    lines.append("- **桌面快捷方式**：双击桌面上的软件图标启动")
    lines.append("- **开始菜单**：从系统开始菜单中找到本软件并点击启动")
    lines.append("")
    lines.append("【请在此插入启动界面截图】")
    lines.append("")

    lines.append("### 3.3 登录系统")
    lines.append("")
    lines.append("1. 启动软件后将显示登录界面")
    lines.append("2. 输入用户名和密码")
    lines.append("3. 点击「登录」按钮进入系统主界面")
    lines.append("")
    lines.append("【请在此插入登录页面截图】")
    lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def generate_features_section(info: dict) -> str:
    """生成功能操作说明部分"""
    sw_name = info.get('software_full_name', '本软件')
    modules = info.get('covered_modules', '')
    core_workflow = info.get('core_workflow', '')
    screenshot_method = info.get('screenshot_method', '暂不截图')

    lines = []
    lines.append("## 四、功能操作说明")
    lines.append("")

    if core_workflow:
        lines.append(f"### 4.0 整体操作流程")
        lines.append("")
        lines.append(f"{sw_name}的主要操作流程如下：{core_workflow}")
        lines.append("")

    if modules:
        module_list = [m.strip() for m in modules.replace('、', '\n').replace(',', '\n').split('\n') if m.strip()]
        for i, module in enumerate(module_list, 1):
            section_num = f"4.{i}"
            lines.append(f"### {section_num} {module}")
            lines.append("")
            lines.append("#### 功能概述")
            lines.append(f"该功能用于{module}。")
            lines.append("")
            lines.append("#### 操作步骤")
            lines.append("")
            lines.append(f"1. 从主界面导航菜单进入「{module}」页面")
            lines.append("2. 页面显示相关数据列表，可按条件进行查询筛选")
            lines.append("3. 点击具体条目可查看详细信息")
            lines.append("4. 支持新增、编辑、删除等基本操作")
            lines.append("")
            if screenshot_method == "暂不截图":
                lines.append(f"【请在此插入「{module}」页面截图】")
            elif screenshot_method == "用户提供":
                lines.append(f"【请在此插入「{module}」页面截图】")
            lines.append("")
    else:
        lines.append(f"> 请根据 {sw_name} 的实际功能模块填写各功能的操作说明。")
        lines.append(f"> 每个功能应包含：功能概述 → 入口位置 → 页面布局 → 操作步骤 → 结果反馈 → 截图位置。")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def generate_faq_section(info: dict) -> str:
    """生成常见问题部分"""
    sw_name = info.get('software_full_name', '本软件')

    lines = []
    lines.append("## 五、常见问题 FAQ")
    lines.append("")

    faq_items = [
        ("Q1：忘记登录密码怎么办？", "请联系系统管理员重置密码。"),
        ("Q2：页面显示异常如何处理？", "请尝试刷新页面或清除浏览器缓存后重新登录。"),
        ("Q3：数据保存失败是什么原因？", "请检查网络连接是否正常，确认必填字段是否都已填写完整。"),
    ]

    for q, a in faq_items:
        lines.append(f"**{q}**")
        lines.append("")
        lines.append(f"{a}")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def generate_contact_section(info: dict) -> str:
    """生成联系方式部分"""
    lines = []
    lines.append("## 六、联系方式")
    lines.append("")
    lines.append(f"如在使用过程中遇到问题，请联系：")
    lines.append("")
    lines.append(f"- 著作权人：{info.get('copyright_owner', '')}")
    lines.append(f"- 联系人：{info.get('contact_person', '')}")
    lines.append("")
    return "\n".join(lines)


def generate_manual_markdown(info: dict, business: Optional[dict] = None) -> str:
    """生成完整用户手册 Markdown"""
    sections = []
    sections.append(generate_cover_section(info))
    sections.append(generate_disclaimer_section(info))
    sections.append(generate_intro_section(info, business))
    sections.append(generate_requirements_section(info))
    sections.append(generate_install_section(info))
    sections.append(generate_features_section(info))
    sections.append(generate_faq_section(info))
    sections.append(generate_contact_section(info))
    return "\n".join(sections)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="生成用户手册 Markdown 草稿")
    parser.add_argument("--info", required=True, help="采集信息 JSON 文件路径")
    parser.add_argument("--business", help="业务理解 JSON 文件路径（可选）")
    parser.add_argument("--out", default="软著申请资料/草稿", help="输出目录")
    args = parser.parse_args()

    info = load_info(args.info)
    business = None
    if args.business:
        try:
            with open(args.business, 'r', encoding='utf-8') as f:
                business = json.load(f)
        except (IOError, json.JSONDecodeError):
            print(f"[WARN] 无法加载业务理解文件: {args.business}")

    manual_md = generate_manual_markdown(info, business)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    sw_name = info.get('software_full_name', '未命名')
    out_path = out_dir / f"{sw_name}_用户手册_草稿.md"
    out_path.write_text(manual_md, encoding='utf-8')

    print(f"[OK] 用户手册 Markdown 草稿已生成: {out_path}")
    print()
    print("[*] 手册包含章节：")
    print("   一、引言（软件概述、适用对象、术语说明）")
    print("   二、系统要求（硬件、操作系统、运行环境）")
    print("   三、安装与启动（安装步骤、启动、登录）")
    print("   四、功能操作说明（各功能模块逐章说明）")
    print("   五、常见问题 FAQ")
    print("   六、联系方式")
    print()
    print(f"[NOTE] 请审阅草稿，确认后可生成正式 PDF。")


if __name__ == "__main__":
    main()
