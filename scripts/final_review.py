#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软著三件套最终复核脚本
检查交付目录中的申请表、用户手册、源码材料是否完整、一致、合规。
用法: python final_review.py --dir <交付目录>
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def check_file_existence(out_dir: Path, sw_name: str, version: str) -> List[str]:
    """检查三件套文件存在性（含 PDF 和 DOCX）"""
    issues = []
    expected = [
        f"{sw_name}_申请表",
        f"{sw_name}_用户手册",
        f"{sw_name}_源代码文档",
    ]
    found_any = False
    for name in expected:
        candidates = list(out_dir.glob(f"{name}*"))
        if candidates:
            found_any = True
            formats_found = [f.suffix for f in candidates]
            print(f"  [✓] {name}: 找到 {len(candidates)} 个文件 ({', '.join(formats_found)})")
        else:
            issues.append(f"[ERR] 缺少: {name}_V{version}.pdf / .docx")
    if not found_any:
        issues.append("[ERR] 正式资料目录中未找到任何三件套文件")
    return issues


def check_consistency(out_dir: Path, info: dict) -> List[str]:
    """检查各文档一致性"""
    issues = []
    sw_name = info.get('software_full_name', '')
    version = info.get('version', '')
    owner = info.get('copyright_owner', '')

    # 检查所有 PDF/TXT 文件
    for f in out_dir.iterdir():
        if f.suffix.lower() in ('.pdf', '.md', '.txt', '.docx'):
            content = ''
            try:
                if f.suffix.lower() == '.md':
                    content = f.read_text(encoding='utf-8', errors='ignore')
                elif f.suffix.lower() == '.txt':
                    content = f.read_text(encoding='utf-8', errors='ignore')
            except (IOError, UnicodeDecodeError):
                pass

            if content:
                # 检查软件名称一致性
                if sw_name and sw_name not in f.name and sw_name not in content[:500]:
                    issues.append(f"[WARN] 文件 {f.name} 中未找到软件全称 \"{sw_name}\"")

    return issues


def check_forbidden_words(out_dir: Path, forbidden_words: List[str]) -> List[str]:
    """检查禁用词残留"""
    if not forbidden_words:
        return []
    issues = []
    for f in out_dir.iterdir():
        if f.suffix.lower() in ('.pdf', '.md', '.txt', '.docx'):
            try:
                content = ''
                if f.suffix.lower() in ('.md', '.txt'):
                    content = f.read_text(encoding='utf-8', errors='ignore')
                if content:
                    for word in forbidden_words:
                        word = word.strip()
                        if word and re.search(re.escape(word), content, re.IGNORECASE):
                            issues.append(f"[ERR] 文件 {f.name} 中发现禁用词: \"{word}\"")
            except (IOError, UnicodeDecodeError):
                pass
    return issues


def check_page_format(out_dir: Path) -> List[str]:
    """检查页码/格式问题"""
    issues = []
    for f in out_dir.iterdir():
        name = f.name.lower()
        # 检查版本号是否在文件名中
        if not re.search(r'v\d+', name):
            issues.append(f"[WARN] 文件 {f.name} 的文件名中可能缺少版本号")

    # 检查 DOCX 文件可读性
    for f in out_dir.glob("*.docx"):
        try:
            from docx import Document
            doc = Document(f)
            para_count = len(doc.paragraphs)
            print(f"  [✓] DOCX 验证: {f.name} ({para_count} 段落)")
        except ImportError:
            pass  # python-docx 未安装，跳过
        except Exception as e:
            issues.append(f"[ERR] DOCX 文件损坏: {f.name} - {e}")

    return issues


def review(out_dir: Path, info: dict = None) -> Tuple[bool, List[str]]:
    """
    执行完整复核
    返回：(是否通过, 问题列表)
    """
    out_dir = Path(out_dir)
    if not out_dir.exists():
        return False, [f"[ERR] 目录不存在: {out_dir}"]

    info = info or {}
    sw_name = info.get('software_full_name', '未知')
    version = info.get('version', 'V1.0')
    forbidden = info.get('forbidden_words', '').strip().split('\n') if info.get('forbidden_words') else []

    all_issues = []
    all_issues.extend(check_file_existence(out_dir, sw_name, version))
    all_issues.extend(check_consistency(out_dir, info))
    all_issues.extend(check_forbidden_words(out_dir, forbidden))
    all_issues.extend(check_page_format(out_dir))

    # 分类
    errors = [i for i in all_issues if i.startswith('[ERR]')]
    warnings = [i for i in all_issues if i.startswith('[WARN]')]

    passed = len(errors) == 0
    return passed, all_issues


def main():
    import argparse

    parser = argparse.ArgumentParser(description="软著三件套最终复核")
    parser.add_argument("--dir", default="软著申请资料/正式资料", help="正式资料目录")
    parser.add_argument("--info", help="采集信息 JSON 路径")
    args = parser.parse_args()

    info = {}
    if args.info:
        try:
            with open(args.info, 'r', encoding='utf-8') as f:
                info = json.load(f)
        except (IOError, json.JSONDecodeError):
            print(f"[WARN] 无法加载采集信息: {args.info}")

    print("=" * 60)
    print("软著三件套最终复核")
    print("=" * 60)
    print(f"复核目录: {args.dir}")
    print()

    passed, issues = review(Path(args.dir), info)

    if issues:
        for issue in issues:
            print(issue)
        print()

    error_count = sum(1 for i in issues if i.startswith('[ERR]'))
    warning_count = sum(1 for i in issues if i.startswith('[WARN]'))

    print("=" * 60)

    if passed:
        print("[OK] 复核通过！三件套资料可以交付。")
    else:
        print(f"[ERR] 复核未通过：{error_count} 个错误, {warning_count} 个警告。")
        print("   请修复上述问题后重新复核。")

    print("=" * 60)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
