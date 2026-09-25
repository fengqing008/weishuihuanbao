# -*- coding: utf-8 -*-
"""生成自包含 HTML 流程图集（PNG base64 内嵌，单文件可移动端查看）"""
import base64, os, argparse

_ap = argparse.ArgumentParser(description='SOP流程图集HTML生成器')
_ap.add_argument('--project', default='示例PPP')
_ap.add_argument('--total', required=True, help='工程量核对图路径')
_ap.add_argument('--diff', required=True, help='差异处理图路径')
_ap.add_argument('--out', default='SOP流程图集.html')
_A = _ap.parse_args()
imgs = [
    (_A.total,
     '一、工程量核对流程', '按部位分流 → 竣工图比对 → 一致直接计量 / 不一致启动签认流程'),
    (_A.diff,
     '二、工程量差异处理流程', '按差异类型 → 编制过程资料 → 四方/三方签章 → 签章齐全性判定'),
]


def b64(p):
    with open(p, 'rb') as f:
        return base64.b64encode(f.read()).decode()


blocks = []
for fn, title, desc in imgs:
    src = 'data:image/png;base64,' + b64(fn)
    blocks.append(f'''  <section class="card">
    <h2>{title}</h2>
    <p class="desc">{desc}</p>
    <div class="imgwrap"><img src="{src}" alt="{title}"></div>
  </section>''')

legend = '''  <section class="card">
    <h2>符号图例</h2>
    <ul class="legend">
      <li><span class="dot"></span>起止节点 —— 流程开始 / 结束</li>
      <li><span class="box"></span>活动节点 —— 具体操作步骤</li>
      <li><span class="dia"></span>判断节点 —— 条件分支</li>
      <li><span class="fold"></span>签章要求 —— 注释说明</li>
      <li><span class="green"></span>计量结果 —— 予以认定</li>
      <li><span class="red"></span>底线规则 —— 不予认定</li>
    </ul>
    <p class="note">底线规则：管网差异须《工程量确认表》四方签章；站点差异须《图纸会审记录》四方签字；接户管差异三方现场复核 —— 签章不全者，结算审计不予认定。</p>
  </section>'''

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>示例PPP竣工结算 SOP 流程图集</title>
<style>
  :root {{ --edge:#5a6c7d; --bg:#f4f6f8; --ink:#22303d; --line:#e2e7ec; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:26px 16px 60px; background:var(--bg);
         font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif; color:var(--ink); }}
  .wrap {{ max-width:1180px; margin:0 auto; }}
  header {{ text-align:center; padding:26px 20px 22px; background:#fff;
            border-radius:16px; box-shadow:0 2px 14px rgba(90,108,125,.10); margin-bottom:22px; }}
  header h1 {{ margin:0 0 8px; font-size:26px; letter-spacing:.5px; }}
  header .sub {{ color:#5a6c7d; font-size:14.5px; }}
  header .meta {{ margin-top:12px; color:#8a97a3; font-size:13px; }}
  .card {{ background:#fff; border-radius:16px; padding:22px 24px 26px;
           box-shadow:0 2px 14px rgba(90,108,125,.10); margin-bottom:20px; }}
  .card h2 {{ margin:0 0 6px; font-size:19px; padding-left:12px;
              border-left:4px solid #2f7f96; line-height:1.2; }}
  .desc {{ margin:6px 0 16px; color:#6a7883; font-size:14px; line-height:1.6; }}
  .imgwrap {{ text-align:center; background:#fbfcfd; border:1px solid var(--line);
              border-radius:12px; padding:10px; overflow:auto; }}
  .imgwrap img {{ max-width:100%; height:auto; border-radius:6px; }}
  .legend {{ list-style:none; padding:0; margin:8px 0 16px; display:grid;
             grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:10px 22px; }}
  .legend li {{ font-size:14px; color:#4a5763; display:flex; align-items:center; gap:9px; }}
  .legend span {{ display:inline-block; width:26px; height:16px; flex:none; }}
  .dot {{ background:#1b1b1b; border-radius:50%; width:14px!important; height:14px!important; }}
  .box {{ background:#fff; border:1.6px solid #5a6c7d; border-radius:5px; }}
  .dia {{ background:#fff3cd; border:1.6px solid #d99b1a;
          clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%); }}
  .fold {{ background:#f7f8e6; border:1.6px solid #a9ab63;
           clip-path:polygon(0 0,100% 0,100% 62%,82% 100%,0 100%); }}
  .green {{ background:#e6f2e2; border:1.6px solid #6da33f; border-radius:5px; }}
  .red {{ background:#fbe0e0; border:1.6px solid #c0392b; border-radius:5px; }}
  .note {{ margin:0; padding:12px 14px; background:#fbe0e0; border-left:4px solid #c0392b;
           border-radius:8px; font-size:13.5px; color:#7d2b23; line-height:1.7; }}
  footer {{ text-align:center; color:#9aa6b0; font-size:12.5px; margin-top:28px; line-height:1.8; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{_A.project}项目工程结算 · SOP 流程图集</h1>
    <div class="sub">适用：施工单位 ／ 设计单位 ／ 监理单位 ／ 建设单位 ／ 审计单位</div>
    <div class="meta">西安绿荫环境工程有限公司　│　V1.0　│　2026-09-11</div>
  </header>
{chr(10).join(blocks)}
{legend}
  <footer>
    依据：《建设工程价款结算暂行办法》（财建〔2004〕369号）、《建设工程工程量清单计价规范》（GB 50500-2013）<br>
    西安绿荫环境工程有限公司 · 工程线（总工办）
  </footer>
</div>
</body>
</html>'''

out = _A.out
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print('OK', round(os.path.getsize(out) / 1024, 1), 'KB')
