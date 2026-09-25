#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOP流程图HTML交互页生成器
- 单文件自包含（mermaid.js@10.9.0 CDN）
- 9种classDef图例+节点形状图例
- 现代卡片式UI
- 响应式设计

Usage:
    python3 sop_flowchart_html.py --mmd-files "总图.mmd" "差异处理.mmd" --output "SOP流程图.html"
"""
import argparse
import os
from pathlib import Path

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="[链接已移除]"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Microsoft YaHei', 'PingFang SC', sans-serif;
            background: #F4F5F7; min-height: 100vh; color: #1F2937; padding: 24px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: #FFFFFF; border-radius: 12px; padding: 28px 32px; margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-top: 4px solid #5A6B7A;
        }}
        .header h1 {{ color: #1F2937; font-size: 24px; font-weight: 700; margin-bottom: 6px; }}
        .header .subtitle {{ color: #6B7280; font-size: 13px; margin-bottom: 12px; }}
        .header .meta {{
            display: flex; gap: 20px; font-size: 12px; color: #6B7280;
            padding-top: 12px; border-top: 1px solid #E5E7EB;
        }}
        .diagram-section {{
            background: #FFFFFF; border-radius: 12px; padding: 28px; margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .diagram-section h2 {{
            color: #1F2937; font-size: 18px; font-weight: 700; margin-bottom: 8px;
            padding-bottom: 10px; border-bottom: 2px solid #E5E7EB;
        }}
        .badge {{
            background: #5A6B7A; color: white; padding: 3px 10px; border-radius: 4px;
            font-size: 11px; font-weight: 600; margin-left: 8px;
        }}
        .description {{
            background: #F9FAFB; border-left: 3px solid #5A6B7A; padding: 14px 16px;
            border-radius: 4px; margin: 16px 0; color: #4B5563; font-size: 13px; line-height: 1.7;
        }}
        .description strong {{ color: #1F2937; font-weight: 600; }}
        .mermaid-container {{
            background: #FAFBFC; border: 1px solid #E5E7EB; border-radius: 8px;
            padding: 20px; overflow-x: auto; text-align: center;
        }}
        .mermaid {{ font-size: 14px; font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; }}
        .legend {{
            background: #F9FAFB; border-radius: 8px; padding: 18px; margin-top: 20px;
            border: 1px solid #E5E7EB;
        }}
        .legend h3 {{ color: #1F2937; font-size: 14px; font-weight: 700; margin-bottom: 12px; }}
        .legend-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;
        }}
        .legend-item {{
            display: flex; align-items: center; gap: 8px; padding: 6px 10px;
            background: white; border-radius: 4px; font-size: 12px; border: 1px solid #E5E7EB;
        }}
        .legend-shape {{
            width: 22px; height: 18px; display: flex; align-items: center;
            justify-content: center; font-size: 10px; font-weight: 700; flex-shrink: 0;
        }}
        .footer {{
            background: #FFFFFF; border-radius: 12px; padding: 18px; text-align: center;
            color: #6B7280; font-size: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .footer a {{ color: #5A6B7A; text-decoration: none; }}
        @media (max-width: 768px) {{
            body {{ padding: 12px; }}
            .header, .diagram-section, .footer {{ padding: 18px; }}
            .header h1 {{ font-size: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <div class="subtitle">{subtitle}</div>
            <div class="meta">
                <span>📄 {doc_no}</span>
                <span>🏢 {contractor}</span>
                <span>📅 {date}</span>
            </div>
        </div>

        {sections}

        <div class="diagram-section">
            <h2>🎨 图例说明</h2>
            <div class="legend">
                <h3>节点形状（7类）</h3>
                <div class="legend-grid">
                    <div class="legend-item"><div class="legend-shape" style="background:#FFFFFF;border:2px solid #5A6B7A;border-radius:50%">●</div>起止节点（圆形）</div>
                    <div class="legend-item"><div class="legend-shape" style="background:#FFFFFF;border:2px solid #5A6B7A">□</div>常规操作（白底矩形）</div>
                    <div class="legend-item"><div class="legend-shape" style="background:#FFF8DC;border:2px solid #D4A574;transform:rotate(45deg);width:14px;height:14px"></div>判断节点（黄色菱形）</div>
                    <div class="legend-item"><div class="legend-shape" style="background:#F5E6C8;border:3px solid #D4A574;clip-path:polygon(25% 0%,75% 0%,100% 50%,75% 100%,25% 100%,0% 50%)">▰</div>关键判断（六边形）</div>
                    <div class="legend-item"><div class="legend-shape" style="background:#FFFFFF;border:2px solid #31859C;transform:skewX(-15deg)">▱</div>汇总节点（青色）</div>
                    <div class="legend-item"><div class="legend-shape" style="background:#E2EFDA;border:2.5px solid #548235;border-radius:4px">✓</div>结果节点（绿色）</div>
                    <div class="legend-item"><div class="legend-shape" style="background:#F5F5DC;border:2px solid #8B8B5A;border-radius:4px">※</div>注释/补充（黄绿）</div>
                    <div class="legend-item"><div class="legend-shape" style="background:#FBE5D6;border:2px solid #C00000;border-radius:4px">!</div>警示/补正（浅红）</div>
                    <div class="legend-item"><div class="legend-shape" style="background:#C00000;border:3px solid #5C0000;color:#fff">⛔</div>底线规则（深红）</div>
                </div>
            </div>
        </div>

        <div class="footer">
            <div>📋 关联文件：{title}.docx</div>
            <div style="margin-top:6px">🏢 {contractor}　|　📅 {date}　|　📐 流程图版本：V7</div>
            <div style="margin-top:6px;color:#9CA3AF">本页面使用 Mermaid.js 渲染，开源免费</div>
        </div>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'base',
            themeVariables: {{
                fontFamily: 'Microsoft YaHei, PingFang SC, sans-serif',
                fontSize: '14px',
                primaryColor: '#FFFFFF',
                primaryTextColor: '#000000',
                primaryBorderColor: '#5A6B7A',
                lineColor: '#5A6B7A',
                background: '#FFFFFF'
            }},
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'linear',
                nodeSpacing: 40,
                rankSpacing: 50
            }}
        }});
    </script>
</body>
</html>
"""

SECTION_TEMPLATE = """
        <div class="diagram-section">
            <h2>{section_title} <span class="badge">{section_badge}</span></h2>
            <div class="description">
                <strong>说明：</strong>{section_desc}
            </div>
            <div class="mermaid-container">
                <div class="mermaid">
{flow_content}
                </div>
            </div>
        </div>
"""


def build_html(title, subtitle, doc_no, contractor, date, sections_data):
    sections_html = ''
    for sec in sections_data:
        mmd_content = Path(sec['mmd_file']).read_text(encoding='utf-8')
        sections_html += SECTION_TEMPLATE.format(
            section_title=sec['title'],
            section_badge=sec['badge'],
            section_desc=sec['desc'],
            flow_content=mmd_content
        )

    return HTML_TEMPLATE.format(
        title=title,
        subtitle=subtitle,
        doc_no=doc_no,
        contractor=contractor,
        date=date,
        sections=sections_html
    )


def main():
    parser = argparse.ArgumentParser(description='SOP流程图HTML生成器')
    parser.add_argument('--mmd-files', nargs='+', required=True, help='mmd源文件列表')
    parser.add_argument('--titles', nargs='+', help='每个mmd对应的章节标题')
    parser.add_argument('--descs', nargs='+', help='每个mmd对应的章节说明')
    parser.add_argument('--output', required=True, help='输出HTML路径')
    parser.add_argument('--title', default='工程结算SOP流程图')
    parser.add_argument('--subtitle', default='SOP流程图 V7')
    parser.add_argument('--doc-no', default='〔2026〕01号')
    parser.add_argument('--contractor', default='XX公司')
    parser.add_argument('--date', default='2026年9月')
    args = parser.parse_args()

    if not args.titles or len(args.titles) != len(args.mmd_files):
        args.titles = [f'流程图{i+1}' for i in range(len(args.mmd_files))]
    if not args.descs or len(args.descs) != len(args.mmd_files):
        args.descs = ['基于本SOP文件自动生成'] * len(args.mmd_files)

    sections_data = []
    badges = ['主流程', '差异处理', '其他', '附录']
    for i, mmd in enumerate(args.mmd_files):
        sections_data.append({
            'title': args.titles[i],
            'badge': badges[i] if i < len(badges) else '流程图',
            'desc': args.descs[i],
            'mmd_file': mmd,
        })

    html_content = build_html(
        title=args.title,
        subtitle=args.subtitle,
        doc_no=args.doc_no,
        contractor=args.contractor,
        date=args.date,
        sections_data=sections_data
    )

    Path(args.output).write_text(html_content, encoding='utf-8')
    size = os.path.getsize(args.output)
    print(f'✓ HTML已生成：{args.output}（{size/1024:.1f}KB）')


if __name__ == '__main__':
    main()
