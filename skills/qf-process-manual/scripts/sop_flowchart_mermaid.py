#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Y型瀑布流程图mermaid生成器
- 基于某区县SOP V7实战蒸馏
- 9种classDef+6种节点形状+商务低饱和
- 四方签字约定自动嵌入

Usage:
    python3 sop_flowchart_mermaid.py --type "总图" --output "总图.mmd"
    python3 sop_flowchart_mermaid.py --type "差异处理" --output "差异处理.mmd"
    python3 sop_flowchart_mermaid.py --type "总图" --render png --output "总图.png"
"""
import argparse
import os
import subprocess
from pathlib import Path

# ============== 公共样式 ==============
COMMON_STYLES = """
    classDef start fill:#FFFFFF,stroke:#5A6B7A,stroke-width:2.5px,color:#000
    classDef principle fill:#FFFFFF,stroke:#5A6B7A,stroke-width:2.5px,color:#000
    classDef decision fill:#FFF8DC,stroke:#D4A574,stroke-width:2.5px,color:#000
    classDef keyDecision fill:#F5E6C8,stroke:#D4A574,stroke-width:3px,color:#000
    classDef normal fill:#FFFFFF,stroke:#5A6B7A,stroke-width:2px,color:#000
    classDef action fill:#FFFFFF,stroke:#31859C,stroke-width:2px,color:#000
    classDef annotation fill:#F5F5DC,stroke:#8B8B5A,stroke-width:2px,color:#000
    classDef warn fill:#FBE5D6,stroke:#C00000,stroke-width:2px,color:#5C0000
    classDef result fill:#E2EFDA,stroke:#548235,stroke-width:2.5px,color:#1F3A0F
    classDef summary fill:#FFFFFF,stroke:#31859C,stroke-width:2.5px,color:#000
    classDef critical fill:#C00000,stroke:#5C0000,stroke-width:3px,color:#fff
    classDef criticalBad fill:#FBE5D6,stroke:#C00000,stroke-width:2.5px,color:#5C0000
    classDef criticalGood fill:#E2EFDA,stroke:#548235,stroke-width:3px,color:#1F3A0F
"""


# ============== 总图模板 ==============
MAIN_FLOW = """flowchart TB
    A([●]):::start
    A --> B[/"**总原则：所有工程量以竣工图为准**"/]:::principle
    B --> C{{"**核对对象属于哪个部位？**"}}:::keyDecision

    C -->|"**管网部分**<br/>主管+检查井+管径+基础"| D1["**按竣工图逐项比对**<br/>管道长度、检查井数量<br/>管径规格、基础形式、接口做法"]:::normal
    D1 --> E1{"与竣工图<br/>是否一致？"}:::decision
    E1 -->|是| F1["**按竣工图直接计量**<br/>纳入第一部分<br/>合同范围内工程量"]:::result
    E1 -->|否| G1["**启动工程量确认流程**<br/>编制《工程量确认表》<br/>四方确认栏版"]:::action
    G1 --> H1[/"**四方签章缺一不可**<br/>**1.施工单位填报签字盖章**<br/>**2.设计单位签字盖章**<br/>**3.监理单位签字盖章**<br/>**4.建设单位签字盖章**"/]:::annotation
    H1 --> F1

    C -->|"**接户管**"| D2["**按三方现场复核**<br/>**确认文件为准**"]:::normal
    D2 --> E2{"与支管核定<br/>文件是否一致？"}:::decision
    E2 -->|是| F2["**按支管核定量计量**<br/>纳入第一部分"]:::result
    E2 -->|否| G2["**启动工程量确认流程**<br/>编制《工程量确认表》<br/>四方确认栏版"]:::action
    G2 --> H2[/"**四方签章缺一不可**<br/>**1.施工单位 2.设计单位**<br/>**3.监理单位 4.建设单位**<br/>须附现场收方或证明资料"/]:::annotation
    H2 --> F2

    C -->|"**站点部分**<br/>构筑物+设备+电气"| D3["**按竣工图核查**<br/>构筑物完整性<br/>设备齐全性<br/>电气自控完整性"]:::normal
    D3 --> E3{"与竣工图<br/>是否一致？<br/>有无缺失？"}:::decision
    E3 -->|是，无缺失| F3["**按竣工图直接计量**<br/>纳入第一部分"]:::result
    E3 -->|否或有缺失| G3["**启动图纸会审流程**<br/>形成《图纸会审记录》<br/>表D.5 按专业分列"]:::action
    G3 --> H3[/"**四方签字缺一不可**<br/>**1.施工单位项目技术负责人签字**<br/>**2.设计单位专业设计负责人签字**<br/>**3.监理单位项目技术负责人签字**<br/>**4.建设单位项目技术负责人签字**"/]:::annotation
    H3 --> F3

    F1 --> I[/"**签认结果汇总**<br/>形成结算工程量计量依据"/]:::summary
    F2 --> I
    F3 --> I
    G1 -.签认.-> I
    G2 -.签认.-> I
    G3 -.签认.-> I
    H1 -.支撑.-> I
    H2 -.支撑.-> I
    H3 -.支撑.-> I

    I --> J["**第一部分 合同内 + 第二部分 合同外**<br/>**合并编制结算书**"]:::summary
    J --> K[/"**进入材料调差计算**<br/>签证内容按当期价<br/>合同内主材按基准价"/]:::summary
    K --> L[/"**进入结算书编制公式**<br/>分部分项+措施项目+规费税金"/]:::summary
    L --> M[/"**进入签字盖章与归档**<br/>四级组卷+电子命名"/]:::summary
    M --> N[/"**进入报送与定案**<br/>施工→建设单位→审计单位"/]:::summary
    N --> O([●]):::start
""" + COMMON_STYLES


# ============== 差异处理模板 ==============
DIFF_FLOW = """flowchart TB
    A([●]):::start
    A --> B[/"**总原则：实际施工与竣工图存在差异**<br/>需办理工程量确认或图纸会审后方可纳入计量"/]:::principle
    B --> C{{"**差异属于哪个部位？**"}}:::keyDecision

    C -->|"**管网工程量差异**<br/>管段+检查井+管径+基础+埋深"| D1[/"**编制《工程量确认表》**<br/>四方确认栏版<br/>按行政村逐项列明<br/>设计长度、实际长度、差异原因"/]:::action
    D1 --> E1[/"**1️⃣ 施工单位**<br/>**项目负责人签字盖章**"/]:::normal
    E1 --> F1[/"**2️⃣ 设计单位**<br/>**专业设计负责人签字盖章**"/]:::normal
    F1 --> G1[/"**3️⃣ 监理单位**<br/>**总监理工程师签字盖章**"/]:::normal
    G1 --> H1[/"**4️⃣ 建设单位**<br/>**项目负责人签字盖章**"/]:::normal
    H1 --> I1{"**四方签章**<br/>**齐全？**"}:::decision
    I1 -->|否| J1[/"**退回补正**<br/>10个工作日内"/]:::warn
    J1 -.补正.-> D1
    I1 -->|是| K1[/"**原件归档**<br/>电子+纸质签章版"/]:::result

    C -->|"**站点工程量差异**<br/>构筑物+设备+电气+给排水缺漏"| D2[/"**整理《图纸会审记录》**<br/>表D.5《图纸会审记录》<br/>按专业分列"/]:::action
    D2 --> E2[/"**1️⃣ 施工单位**<br/>**项目技术负责人签字**"/]:::normal
    E2 --> F2[/"**2️⃣ 监理单位**<br/>**项目技术负责人签字**"/]:::normal
    F2 --> G2[/"**3️⃣ 设计单位**<br/>**专业设计负责人签字**"/]:::normal
    G2 --> H2[/"**4️⃣ 建设单位**<br/>**项目技术负责人签字**"/]:::normal
    H2 --> I2{"**四方签字**<br/>**齐全？**"}:::decision
    I2 -->|否| J2[/"**退回补正**<br/>10个工作日内"/]:::warn
    J2 -.补正.-> D2
    I2 -->|是| K2[/"**原件归档**"/]:::result

    K1 --> L[/"**结算运用**<br/>**第一部分：按竣工图量编制**<br/>**第二部分：按签认结果调增或调减**"/]:::summary
    K2 --> L

    L --> M{{"**底线规则**<br/>**四方签字齐全？**"}}:::critical
    M -->|否| N[/"**⛔ 结算审计不予认定**"/]:::criticalBad
    M -->|是| O[/"**✅ 纳入结算**<br/>**进入报送与定案流程**"/]:::criticalGood

    O --> P([●]):::start
""" + COMMON_STYLES


def render_png(mmd_path, png_path, width=1800, theme='zinc-light'):
    """调用pretty-mermaid技能渲染PNG"""
    script = os.environ.get('PRETTY_MERMAID_RENDER') or str(
        Path(__file__).resolve().parents[2] / 'pretty-mermaid' / 'scripts' / 'render.mjs')
    if not Path(script).exists():
        return f'✗ pretty-mermaid技能未安装，请先安装'
    cmd = ['node', script, '--input', str(mmd_path), '--output', str(png_path),
           '--theme', theme, '--width', str(width), '--format', 'png']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            size = os.path.getsize(png_path) if os.path.exists(png_path) else 0
            return f'✓ PNG已渲染：{png_path}（{size/1024:.1f}KB）'
        return f'✗ 渲染失败：{result.stderr}'
    except Exception as e:
        return f'✗ 渲染异常：{e}'


def main():
    parser = argparse.ArgumentParser(description='Y型瀑布流程图生成器')
    parser.add_argument('--type', required=True, choices=['总图', '差异处理'], help='流程图类型')
    parser.add_argument('--output', required=True, help='输出文件路径（.mmd或.png）')
    parser.add_argument('--render', choices=['mmd', 'png'], default='mmd', help='输出格式')
    parser.add_argument('--theme', default='zinc-light', help='pretty-mermaid主题')
    parser.add_argument('--width', type=int, default=1800, help='PNG宽度')
    args = parser.parse_args()

    if args.type == '总图':
        mmd_content = MAIN_FLOW
    else:
        mmd_content = DIFF_FLOW

    output_path = Path(args.output)
    if args.render == 'png' or output_path.suffix == '.png':
        # 先生成mmd，再用pretty-mermaid渲染
        mmd_path = output_path.with_suffix('.mmd')
        mmd_path.write_text(mmd_content, encoding='utf-8')
        print(f'✓ MMD已保存：{mmd_path}')
        if output_path.suffix == '.png':
            print(render_png(str(mmd_path), str(output_path), args.width, args.theme))
        else:
            # output是.mmd但要求PNG
            png_path = output_path.with_suffix('.png')
            print(render_png(str(mmd_path), str(png_path), args.width, args.theme))
    else:
        output_path.write_text(mmd_content, encoding='utf-8')
        size = os.path.getsize(output_path)
        print(f'✓ 已生成：{output_path}（{size/1024:.1f}KB）')


if __name__ == '__main__':
    main()
