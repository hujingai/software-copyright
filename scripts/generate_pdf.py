#!/usr/bin/env python3
"""
PDF Generator for Software Copyright Documents
软著文档 PDF 生成器

Requires: pip install reportlab
"""

import os
import sys
from pathlib import Path
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     PageBreak, Table, TableStyle, KeepTogether)
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, Frame
except ImportError:
    print("Error: reportlab is required. Install with: pip install reportlab")
    sys.exit(1)


# Try to register Chinese fonts
FONT_REGISTERED = False
FONT_NAME = 'Helvetica'
FONT_NAME_BOLD = 'Helvetica-Bold'
MONO_FONT = 'Courier'

# Common Chinese font paths on Windows
_CHINESE_FONT_PATHS = [
    ('SimSun', 'C:/Windows/Fonts/simsun.ttc'),
    ('SimHei', 'C:/Windows/Fonts/simhei.ttf'),
    ('SimFang', 'C:/Windows/Fonts/simfang.ttf'),
    ('KaiTi', 'C:/Windows/Fonts/simkai.ttf'),
    ('Microsoft YaHei', 'C:/Windows/Fonts/msyh.ttc'),
    ('Source Han Sans', 'C:/Windows/Fonts/SourceHanSansSC-Regular.otf'),
]

def _register_fonts():
    global FONT_REGISTERED, FONT_NAME, FONT_NAME_BOLD, MONO_FONT
    if FONT_REGISTERED:
        return

    for name, path in _CHINESE_FONT_PATHS:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                FONT_REGISTERED = True
                FONT_NAME = name
                FONT_NAME_BOLD = name
                if name == 'SimSun':
                    MONO_FONT = name
                print(f"Registered font: {name} from {path}")
                return
            except Exception:
                continue

    print("Warning: No Chinese font found. Chinese characters may not render correctly.")


def get_styles():
    """Get paragraph styles for Chinese documents."""
    _register_fonts()
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'CoverTitle', fontName=FONT_NAME_BOLD, fontSize=22,
        alignment=TA_CENTER, spaceAfter=20, leading=30
    ))
    styles.add(ParagraphStyle(
        'CoverSubtitle', fontName=FONT_NAME, fontSize=14,
        alignment=TA_CENTER, spaceAfter=10, leading=20
    ))
    styles.add(ParagraphStyle(
        'H1', fontName=FONT_NAME_BOLD, fontSize=16,
        spaceBefore=20, spaceAfter=10, leading=24
    ))
    styles.add(ParagraphStyle(
        'H2', fontName=FONT_NAME_BOLD, fontSize=14,
        spaceBefore=15, spaceAfter=8, leading=20
    ))
    styles.add(ParagraphStyle(
        'H3', fontName=FONT_NAME_BOLD, fontSize=12,
        spaceBefore=10, spaceAfter=6, leading=18
    ))
    styles.add(ParagraphStyle(
        'BodyCN', fontName=FONT_NAME, fontSize=12,
        spaceBefore=4, spaceAfter=4, leading=20,
        firstLineIndent=2 * 12  # 2 chars indent
    ))
    code_style = ParagraphStyle(
        'SourceCode', fontName=MONO_FONT, fontSize=8,
        spaceBefore=0, spaceAfter=0, leading=10,
        leftIndent=5
    )
    styles.add(code_style)
    styles.add(ParagraphStyle(
        'CodeHeader', fontName=FONT_NAME, fontSize=7,
        spaceBefore=2, spaceAfter=2, leading=9,
        textColor=colors.grey
    ))
    styles.add(ParagraphStyle(
        'PageNumber', fontName=FONT_NAME, fontSize=9,
        alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'Footer', fontName=FONT_NAME, fontSize=9,
        alignment=TA_CENTER, textColor=colors.grey
    ))
    return styles


def build_source_doc_pdf(output_path, data, software_name, version):
    """Build source code documentation PDF."""
    _register_fonts()
    styles = get_styles()

    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=3 * cm, rightMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2 * cm,
        title=f'{software_name} 源代码文档'
    )

    story = []

    # Cover page
    story.append(Spacer(1, 6 * cm))
    story.append(Paragraph(f'{software_name}', styles['CoverTitle']))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f'版本号：{version}', styles['CoverSubtitle']))
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph('源代码文档', styles['CoverTitle']))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(f'提交页数：{len(data["selected_pages"])} 页', styles['CoverSubtitle']))
    story.append(Paragraph(
        '提交方式：全部提交' if data['is_full_submission'] else '提交方式：前30页 + 后30页',
        styles['CoverSubtitle']
    ))
    story.append(Paragraph(f'总行数：{data["total_lines"]} 行', styles['CoverSubtitle']))
    story.append(Paragraph(f'总页数：{data["total_pages"]} 页', styles['CoverSubtitle']))
    story.append(Paragraph(f'生成日期：{data["generated_date"]}', styles['CoverSubtitle']))
    story.append(PageBreak())

    # Source code pages
    for i, page_lines in enumerate(data['selected_pages'], 1):
        # Page header
        header_text = f'{software_name} {version}'
        story.append(Paragraph(header_text, styles['CodeHeader']))
        story.append(Spacer(1, 3))

        # Code lines
        for line in page_lines:
            # Escape HTML special chars
            safe_line = (line.replace('&', '&amp;')
                            .replace('<', '&lt;')
                            .replace('>', '&gt;')
                            .replace(' ', '&nbsp;')
                            .replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;'))
            if safe_line == '' or safe_line == '&nbsp;':
                safe_line = '&nbsp;'
            story.append(Paragraph(safe_line, styles['SourceCode']))

        # Page footer
        story.append(Spacer(1, 5))
        story.append(Paragraph(f'第 {i} 页', styles['PageNumber']))

        if i < len(data['selected_pages']):
            story.append(PageBreak())

    doc.build(story)
    print(f"PDF saved to: {output_path}")


def build_manual_pdf(output_path, software_name, version, sections):
    """Build user manual PDF."""
    _register_fonts()
    styles = get_styles()

    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
        title=f'{software_name} 用户使用说明书'
    )

    story = []

    # Cover
    story.append(Spacer(1, 5 * cm))
    story.append(Paragraph(f'{software_name}', styles['CoverTitle']))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f'{version}', styles['CoverSubtitle']))
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph('用户使用说明书', styles['CoverTitle']))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(f'日期：{datetime.now().strftime("%Y-%m-%d")}', styles['CoverSubtitle']))
    story.append(PageBreak())

    # Sections
    for section in sections:
        title = section.get('title', '')
        level = section.get('level', 1)
        content = section.get('content', '')

        if level == 1:
            style = styles['H1']
        elif level == 2:
            style = styles['H2']
        elif level == 3:
            style = styles['H3']
        else:
            style = styles['BodyCN']

        story.append(Paragraph(title, style))

        if isinstance(content, list):
            for para in content:
                story.append(Paragraph(para, styles['BodyCN']))
        elif content:
            story.append(Paragraph(content, styles['BodyCN']))

        story.append(Spacer(1, 8))

    doc.build(story)
    print(f"PDF saved to: {output_path}")


def build_application_form_pdf(output_path, form_data):
    """Build application form PDF."""
    _register_fonts()
    styles = get_styles()

    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title='计算机软件著作权登记申请表'
    )

    story = []

    # Title
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph('计算机软件著作权登记申请表', styles['CoverTitle']))
    story.append(Spacer(1, 1 * cm))

    # Form fields
    fields = [
        ('软件全称', form_data.get('software_name', '')),
        ('简称', form_data.get('short_name', '')),
        ('版本号', form_data.get('version', 'V1.0')),
        ('分类号', form_data.get('category_code', '')),
        ('开发完成日期', form_data.get('completion_date', '')),
        ('首次发表日期', form_data.get('publish_date', '（未发表）')),
        ('硬件环境', form_data.get('hardware_env', '')),
        ('软件环境', form_data.get('software_env', '')),
        ('编程语言', form_data.get('programming_language', '')),
        ('源代码行数', str(form_data.get('source_lines', ''))),
        ('权利范围', form_data.get('right_scope', '全部权利')),
    ]

    # Applicant info
    story.append(Paragraph('一、软件基本信息', styles['H2']))
    table_data = []
    for label, value in fields:
        table_data.append([
            Paragraph(f'<b>{label}</b>', styles['BodyCN']),
            Paragraph(value or '___________', styles['BodyCN'])
        ])

    t = Table(table_data, colWidths=[4 * cm, 10 * cm])
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
    ]))
    story.append(t)
    story.append(Spacer(1, 1 * cm))

    # Applicant info
    story.append(Paragraph('二、著作权人信息', styles['H2']))
    applicant_fields = [
        ('姓名/名称', form_data.get('owner_name', '')),
        ('证件类型', form_data.get('owner_id_type', '身份证')),
        ('证件号码', form_data.get('owner_id_number', '')),
        ('地址', form_data.get('owner_address', '')),
        ('联系电话', form_data.get('owner_phone', '')),
    ]

    table_data2 = []
    for label, value in applicant_fields:
        table_data2.append([
            Paragraph(f'<b>{label}</b>', styles['BodyCN']),
            Paragraph(value or '___________', styles['BodyCN'])
        ])

    t2 = Table(table_data2, colWidths=[4 * cm, 10 * cm])
    t2.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
    ]))
    story.append(t2)
    story.append(Spacer(1, 1 * cm))

    # Signature area
    story.append(Paragraph('三、申请人声明', styles['H2']))
    story.append(Paragraph(
        '本人/本单位保证所提交的申请材料真实、准确、完整，所申请的软件为本人/本单位独立开发，'
        '未侵犯他人合法权益。如有不实之处，本人/本单位愿承担由此引起的法律责任。',
        styles['BodyCN']
    ))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph('申请人签字/盖章：________________', styles['BodyCN']))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f'日期：{"____年____月____日"}', styles['BodyCN']))

    doc.build(story)
    print(f"PDF saved to: {output_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='软著文档PDF生成器')
    subparsers = parser.add_subparsers(dest='command', help='Document type')

    # Source code doc
    source_parser = subparsers.add_parser('source', help='Generate source code PDF')
    source_parser.add_argument('--input', required=True, help='Input JSON file (from generate_source_doc.py)')
    source_parser.add_argument('--output', required=True, help='Output PDF path')
    source_parser.add_argument('--name', required=True, help='Software name')
    source_parser.add_argument('--version', default='V1.0', help='Version')

    # User manual
    manual_parser = subparsers.add_parser('manual', help='Generate user manual PDF')
    manual_parser.add_argument('--output', required=True, help='Output PDF path')
    manual_parser.add_argument('--name', required=True, help='Software name')
    manual_parser.add_argument('--version', default='V1.0', help='Version')
    manual_parser.add_argument('--input', required=True, help='Input JSON file with sections')

    # Application form
    form_parser = subparsers.add_parser('form', help='Generate application form PDF')
    form_parser.add_argument('--output', required=True, help='Output PDF path')
    form_parser.add_argument('--input', required=True, help='Input JSON file with form data')

    args = parser.parse_args()

    if args.command == 'source':
        import json
        with open(args.input, 'r', encoding='utf-8') as f:
            raw = json.load(f)

        # Normalize JSON format: support both flat and wrapped structures
        if 'metadata' in raw:
            data = raw['metadata'].copy()
            data['selected_pages'] = [p['lines'] for p in raw['pages']]
            data['file_index'] = raw.get('file_index', [])
        else:
            data = raw
        build_source_doc_pdf(args.output, data, args.name, args.version)

    elif args.command == 'manual':
        import json
        with open(args.input, 'r', encoding='utf-8') as f:
            sections = json.load(f)
        build_manual_pdf(args.output, args.name, args.version, sections)

    elif args.command == 'form':
        import json
        with open(args.input, 'r', encoding='utf-8') as f:
            form_data = json.load(f)
        build_application_form_pdf(args.output, form_data)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
