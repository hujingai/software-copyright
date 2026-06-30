#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软著源代码文档生成器（增强版）
从项目目录抽取源代码，按前30页+后30页格式生成PDF。
支持多种语言、行段选择、前后端分类、安全清理。
用法: python generate_source_doc.py --project <项目路径> [--info <采集信息JSON>] [--out <输出目录>]
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, List, Optional, Tuple

# 排除目录
EXCLUDE_DIRS = {
    'node_modules', 'dist', 'build', '.git', '__pycache__', '.idea',
    'target', 'vendor', '.gradle', 'coverage', '.next', '.nuxt',
    'output', 'out', '.cache', '.turbo', '.codebuddy', '.codex',
    '软著申请资料', '软件著作权申请资料',
}

# 排除的文件名模式
EXCLUDE_FILE_PATTERNS = [
    r'\.min\.', r'\.bundle\.', r'\.chunk\.', r'\.map$', r'\.lock$',
    r'package-lock', r'yarn\.lock', r'pnpm-lock',
    r'\.test\.', r'\.spec\.', r'\.stories\.',
]

# 排除的后缀
EXCLUDE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp',
    '.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv',
    '.ttf', '.woff', '.woff2', '.eot', '.otf',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.tar', '.gz', '.rar', '.7z', '.jar', '.war',
    '.exe', '.dll', '.so', '.dylib', '.wasm', '.bin',
    '.db', '.sqlite', '.sqlite3', '.mdb',
    '.log', '.txt',
}

# 编程语言后缀
LANGUAGE_EXTS = {
    '.java', '.py', '.pyw', '.js', '.jsx', '.ts', '.tsx', '.vue',
    '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.kts',
    '.c', '.h', '.cpp', '.cc', '.cxx', '.hpp', '.hxx',
    '.cs', '.dart', '.scala', '.sc', '.sql', '.r', '.m',
    '.lua', '.sh', '.bash', '.zsh', '.ps1',
    '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.css', '.scss', '.less', '.sass', '.html', '.htm',
    '.json',
}


def should_exclude(file_path: Path, project_root: Path) -> bool:
    """判断文件是否应排除"""
    parts = file_path.relative_to(project_root).parts
    for part in parts:
        if part.startswith('.') and part != '.':
            return True
        if part in EXCLUDE_DIRS:
            return True
    # 后缀排除
    if file_path.suffix.lower() in EXCLUDE_EXTENSIONS:
        return True
    # 文件名模式排除
    name = file_path.name
    for pat in EXCLUDE_FILE_PATTERNS:
        if re.search(pat, name):
            return True
    # 必须是可识别的源码文件
    if file_path.suffix.lower() not in LANGUAGE_EXTS:
        return False  # 未知后缀不排除，让后续判断
    return False


def is_frontend(file_path: Path, project_root: Path) -> bool:
    """判断是否为前端文件"""
    frontend_indicators = {'.vue', '.tsx', '.jsx', '.css', '.scss', '.less', '.sass', '.html', '.htm'}
    if file_path.suffix.lower() in frontend_indicators:
        return True
    path_str = str(file_path.relative_to(project_root)).lower().replace('\\', '/')
    frontend_dirs = {'pages/', 'views/', 'components/', 'frontend/', 'web/', 'public/', 'assets/'}
    return any(d in path_str for d in frontend_dirs)


def is_backend(file_path: Path, project_root: Path) -> bool:
    """判断是否为后端文件"""
    backend_indicators = {'.java', '.go', '.rb', '.php'}
    if file_path.suffix.lower() in backend_indicators:
        return True
    path_str = str(file_path.relative_to(project_root)).lower().replace('\\', '/')
    backend_dirs = {'controllers/', 'services/', 'models/', 'entities/', 'repository/', 'dao/', 'mapper/', 'server/', 'api/'}
    return any(d in path_str for d in backend_dirs)


def clean_source_content(content: str) -> str:
    """清理源代码中的敏感信息"""
    # 移除 API Key
    content = re.sub(r'(api[_-]?key|apikey|secret|token|password|passwd)\s*[:=]\s*["\'][^"\']+["\']',
                     r'\1: "***HIDDEN***"', content, flags=re.IGNORECASE)
    # 移除 Bearer token
    content = re.sub(r'sk-[a-zA-Z0-9]{32,}', 'sk-***HIDDEN***', content)
    # 移除超长 base64 字符串（可能的密钥）
    content = re.sub(r'[A-Za-z0-9+/=]{40,}', '***HIDDEN***', content)
    # 清理尾随空格
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
    # 将多个连续空行合并为最多2个空行
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    return content


def paginate_code(lines: List[str], lines_per_page: int = 50) -> List[Tuple[int, List[str]]]:
    """
    分页：每 lines_per_page 行一页
    返回 [(页码, [代码行]), ...]
    """
    pages = []
    for i in range(0, len(lines), lines_per_page):
        page_lines = lines[i:i + lines_per_page]
        pages.append((len(pages) + 1, page_lines))
    return pages


def extract_source_pages(
    all_files: List[Tuple[Path, List[str], bool]],  # (路径, 代码行列表, 是否前端)
    lines_per_page: int = 50,
    source_order: str = "frontend_first",
    max_pages: int = 30,
) -> Dict:
    """
    从源码文件列表中提取前30页和后30页
    返回: dict with 'first_30_pages', 'last_30_pages', 'total_pages', 'total_files'
    """
    # 排序：前端在前或后端在前
    def sort_key(item):
        path, lines, is_fe = item
        if source_order == "frontend_first":
            return (0 if is_fe else 1, str(path))
        else:
            return (1 if is_fe else 0, str(path))

    sorted_files = sorted(all_files, key=sort_key)

    # 逐文件分页
    all_pages = []  # [(文件路径, 页码, 代码行), ...]
    page_counter = 0

    for file_path, file_lines, is_fe in sorted_files:
        if not file_lines:
            continue
        file_pages = paginate_code(file_lines, lines_per_page)
        for _, page_lines in file_pages:
            page_counter += 1
            all_pages.append({
                "page_number": page_counter,
                "source_file": str(file_path),
                "is_frontend": is_fe,
                "line_count": len(page_lines),
                "lines": page_lines,
            })

    total_pages = len(all_pages)

    if total_pages <= max_pages * 2:
        # 不足60页，全交
        return {
            "all_pages": all_pages,
            "first_N_pages": all_pages,
            "last_N_pages": [],
            "total_pages": total_pages,
            "strategy": "submit_all",
            "total_files_scanned": len(sorted_files),
        }

    # 取前30页和后30页
    first_30 = all_pages[:max_pages]
    last_30 = all_pages[-max_pages:]

    return {
        "all_pages": all_pages,
        "first_N_pages": first_30,
        "last_N_pages": last_30,
        "total_pages": total_pages,
        "strategy": f"first_{max_pages}_last_{max_pages}",
        "total_files_scanned": len(sorted_files),
    }


def load_info(info_path: str) -> dict:
    """加载采集信息"""
    with open(info_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_source_report_markdown(result: dict, sw_name: str, version: str,
                                     owner: str, date_str: str, lines_per_page: int = 50) -> str:
    """生成源码追溯报告 Markdown"""
    lines = []
    lines.append(f"# 源代码追溯报告")
    lines.append("")
    lines.append(f"- **软件名称**：{sw_name}")
    lines.append(f"- **版本号**：{version}")
    lines.append(f"- **著作权人**：{owner}")
    lines.append(f"- **生成日期**：{date_str}")
    lines.append(f"- **代码总行数**：{result.get('total_lines', 0):,} 行")
    lines.append(f"- **源码文件数**：{result.get('total_files_scanned', 0)} 个")
    lines.append(f"- **总页数**：{result['total_pages']} 页")
    lines.append(f"- **抽取策略**：{result['strategy']}")
    lines.append(f"- **每页行数**：{lines_per_page}")
    lines.append("")

    lines.append("## 抽取页码清单")
    lines.append("")
    lines.append("| 页码 | 源文件 | 行数 | 前端/后端 |")
    lines.append("|------|--------|------|-----------|")

    for page in result.get('first_N_pages', []) + result.get('last_N_pages', []):
        fe = "前端" if page.get("is_frontend") else "后端"
        fname = Path(page['source_file']).name
        lines.append(f"| {page['page_number']} | {fname} | {page['line_count']} | {fe} |")

    lines.append("")
    return "\n".join(lines)


def generate_pdf_from_pages(
    result: dict,
    sw_name: str,
    version: str,
    output_path: Path,
    lines_per_page: int = 50,
) -> bool:
    """
    使用 reportlab 生成 PDF
    如果无法导入 reportlab，生成 TXT 作为备选
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                         PageBreak, Table, TableStyle, Preformatted)
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    except ImportError:
        print("[WARN] reportlab 未安装，生成 TXT 替代 PDF。")
        print("   安装: pip install reportlab")
        return generate_txt_from_pages(result, sw_name, version, output_path, lines_per_page)

    pdf_path = output_path
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=3 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # 尝试注册中文字体
    try:
        pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
        chinese_font = 'SimSun'
    except Exception:
        try:
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            chinese_font = 'STSong-Light'
        except Exception:
            chinese_font = 'Helvetica'

    # 样式
    title_style = ParagraphStyle(
        'TitleStyle', fontName=chinese_font, fontSize=16,
        leading=24, alignment=TA_CENTER, spaceAfter=20
    )
    code_style = ParagraphStyle(
        'CodeStyle', fontName='Courier', fontSize=8,
        leading=10, leftIndent=0, spaceBefore=0, spaceAfter=0
    )
    header_style = ParagraphStyle(
        'HeaderStyle', fontName=chinese_font, fontSize=9,
        leading=14, alignment=TA_CENTER
    )
    footer_style = ParagraphStyle(
        'FooterStyle', fontName=chinese_font, fontSize=8,
        leading=10, alignment=TA_CENTER, textColor=colors.grey
    )

    story = []

    # 封面
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph(f"{sw_name}", title_style))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"版本：{version}", ParagraphStyle(
        'ver', fontName=chinese_font, fontSize=12, leading=18, alignment=TA_CENTER)))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("源代码文档", ParagraphStyle(
        'subtitle', fontName=chinese_font, fontSize=18, leading=27, alignment=TA_CENTER)))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(f"前30页 + 后30页  |  共 {result['total_pages']} 页",
                           ParagraphStyle('info', fontName=chinese_font, fontSize=10,
                                          leading=15, alignment=TA_CENTER)))
    story.append(PageBreak())

    # 正文：前30页
    for section_label, pages in [("源代码文档 — 前30页", result.get('first_N_pages', [])),
                                  ("源代码文档 — 后30页", result.get('last_N_pages', []))]:
        if not pages:
            continue

        if section_label != "源代码文档 — 前30页":
            story.append(PageBreak())

        story.append(Paragraph(section_label, ParagraphStyle(
            'section', fontName=chinese_font, fontSize=12, leading=18,
            alignment=TA_CENTER, spaceAfter=12)))
        story.append(Spacer(1, 0.5 * cm))

        for page in pages:
            # 页眉：软件名 + 版本号
            story.append(Paragraph(
                f"{sw_name} V{version}　　　　　　　　　　　　　　　　　　第 {page['page_number']} 页",
                header_style
            ))
            story.append(Spacer(1, 0.2 * cm))

            # 代码行
            for ln in page['lines']:
                # HTML 转义
                safe_line = ln.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # 处理空格
                safe_line = safe_line.replace(' ', '&nbsp;')
                # 截断过长行
                if len(safe_line) > 120:
                    safe_line = safe_line[:120]
                story.append(Paragraph(safe_line, code_style))

            # 页脚：文件名
            fname = Path(page['source_file']).name
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph(f"文件：{fname}", footer_style))
            story.append(Spacer(1, 0.3 * cm))

    # 生成 PDF
    doc.build(story)
    print(f"[OK] 源代码 PDF 已生成: {pdf_path}")
    return True


def generate_txt_from_pages(result: dict, sw_name: str, version: str,
                             output_path: Path, lines_per_page: int = 50) -> bool:
    """备选方案：生成 TXT 文件"""
    txt_path = output_path.with_suffix('.txt')
    lines = []
    lines.append(f"{sw_name} V{version} — 源代码文档（前30页+后30页）")
    lines.append("=" * 60)
    lines.append("")

    for section_label, pages in [("=== 前30页 ===", result.get('first_N_pages', [])),
                                  ("=== 后30页 ===", result.get('last_N_pages', []))]:
        if not pages:
            continue
        lines.append(section_label)
        lines.append("")
        for page in pages:
            fname = Path(page['source_file']).name
            lines.append(f"--- 第 {page['page_number']} 页 | 文件: {fname} ---")
            for ln in page['lines']:
                lines.append(ln)
            lines.append("")

    txt_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"[OK] 源代码 TXT 已生成: {txt_path}")
    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description="生成软著源代码文档")
    parser.add_argument("--project", required=True, help="项目根目录路径")
    parser.add_argument("--info", help="采集信息 JSON 路径")
    parser.add_argument("--out", default="软著申请资料/正式资料", help="输出目录")
    parser.add_argument("--lines-per-page", type=int, default=50, help="每页代码行数 (默认50)")
    parser.add_argument("--max-pages", type=int, default=30, help="前/后各取多少页 (默认30)")
    parser.add_argument("--order", choices=["frontend_first", "backend_first", "mixed"],
                        default="frontend_first", help="源码排列顺序")
    parser.add_argument("--format", choices=["pdf", "txt", "docx", "both", "all"],
                        default="all", help="输出格式 (all = pdf+docx)")
    args = parser.parse_args()

    project_root = Path(args.project)
    if not project_root.exists():
        print(f"[ERR] 项目路径不存在: {project_root}")
        sys.exit(1)

    sw_name = "未命名软件"
    version = "V1.0"
    owner = ""

    # 从采集信息加载
    if args.info:
        try:
            info = load_info(args.info)
            sw_name = info.get('software_full_name', sw_name)
            version = info.get('version', version)
            owner = info.get('copyright_owner', owner)
        except (IOError, json.JSONDecodeError):
            print("[WARN] 无法加载采集信息，使用默认值")

    print(f"[*] 扫描项目: {project_root}")
    print(f"   软件名: {sw_name}")
    print(f"   版本: {version}")
    print(f"   每页行数: {args.lines_per_page}")
    print(f"   抽取策略: 前{args.max_pages} + 后{args.max_pages}")
    print()

    # 收集所有源码文件
    all_files = []
    total_lines = 0
    ext_counts = Counter()

    for file_path in project_root.rglob('*'):
        if not file_path.is_file():
            continue
        if should_exclude(file_path, project_root):
            continue

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            content = clean_source_content(content)
            code_lines = [l for l in content.split('\n')]
        except (IOError, UnicodeDecodeError):
            continue

        total_lines += len(code_lines)
        ext_counts[file_path.suffix.lower()] += 1
        is_fe = is_frontend(file_path, project_root)
        all_files.append((file_path, code_lines, is_fe))

    print(f"[*] 扫描结果:")
    print(f"   源码文件: {len(all_files)} 个")
    print(f"   总行数: {total_lines:,} 行")
    if ext_counts:
        print(f"   主要语言: {', '.join(f'{ext}({cnt})' for ext, cnt in ext_counts.most_common(5))}")

    # 分页提取
    result = extract_source_pages(all_files, args.lines_per_page, args.order, args.max_pages)
    result['total_lines'] = total_lines

    print(f"\n[*] 分页结果:")
    print(f"   总页数: {result['total_pages']} 页")
    print(f"   策略: {result['strategy']}")
    if result['strategy'] == 'submit_all':
        print(f"   不足{args.max_pages * 2}页，提交全部")
    else:
        print(f"   前{args.max_pages}页 + 后{args.max_pages}页")

    # 生成文件
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime
    date_str = datetime.now().strftime('%Y-%m-%d')

    # 生成追溯报告
    report_md = generate_source_report_markdown(
        result, sw_name, version, owner, date_str, args.lines_per_page
    )
    report_path = out_dir / f"{sw_name}_源码追溯报告.md"
    report_path.write_text(report_md, encoding='utf-8')
    print(f"\n[OK] 源码追溯报告: {report_path}")

    # 保存分页数据 JSON（供 DOCX 生成器使用）
    pages_json_path = out_dir / f"{sw_name}_源代码_分页数据.json"
    # 转换 result 为可序列化格式
    serializable_result = {
        "software_name": sw_name,
        "version": version,
        "total_pages": result["total_pages"],
        "total_lines": result.get("total_lines", 0),
        "strategy": result["strategy"],
        "total_files_scanned": result.get("total_files_scanned", 0),
        "first_N_pages": result.get("first_N_pages", []),
        "last_N_pages": result.get("last_N_pages", []),
        "all_pages": result.get("all_pages", []),
        "generated_date": date_str,
    }
    pages_json_path.write_text(
        json.dumps(serializable_result, ensure_ascii=False, indent=2, default=str),
        encoding='utf-8'
    )
    print(f"[OK] 分页数据 JSON: {pages_json_path}")

    # 生成 PDF
    if args.format in ("pdf", "both", "all"):
        pdf_path = out_dir / f"{sw_name}_源代码文档_V{version}.pdf"
        generate_pdf_from_pages(result, sw_name, version, pdf_path, args.lines_per_page)

    # 生成 DOCX
    if args.format in ("docx", "both", "all"):
        try:
            from generate_source_docx import build_source_docx as build_src_docx
            docx_path = out_dir / f"{sw_name}_源代码文档_V{version}.docx"
            build_src_docx(str(docx_path), serializable_result, sw_name, version)
        except ImportError as e:
            print(f"[WARN] 无法生成 DOCX: {e}")
            print("  请运行: pip install python-docx")

    if args.format in ("txt", "both"):
        txt_path = out_dir / f"{sw_name}_源代码文档_V{version}.txt"
        generate_txt_from_pages(result, sw_name, version, txt_path, args.lines_per_page)


if __name__ == "__main__":
    main()
