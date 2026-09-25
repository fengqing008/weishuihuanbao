#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身价罗盘（Net Worth Compass）· HTML 报告生成器 v3.0
====================================================
互动版新增：
  1) 资产可手动增删改（名称 / 类别 / 金额），净资产与分位实时刷新
  2) 房产估价：输入小区名 + 建筑面积 → 自动匹配房价库 → 一键填入资产
  3) 地区自选（省 → 市 → 区县）

用法：
  python3 nwc_html.py --input result.json --out report.html [--interactive]
"""
import json
import html
import argparse
import os
from string import Template

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_PATH = os.path.join(BASE_DIR, "assets", "baseline.json")
HOUSING_PATH = os.path.join(BASE_DIR, "assets", "housing.json")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,"PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;
  background:#eef2f7; color:#1f2937; line-height:1.6; padding:24px 12px; }
.wrap { max-width:880px; margin:0 auto; }
.card { background:#fff; border-radius:16px; box-shadow:0 4px 18px rgba(15,23,42,.07);
  padding:24px; margin-bottom:18px; }
.hero { background:linear-gradient(135deg,#1e3a8a 0%,#0e7490 55%,#0f766e 100%);
  color:#fff; border-radius:16px; padding:28px 26px; margin-bottom:18px;
  box-shadow:0 10px 26px rgba(14,116,144,.28); }
.hero h1 { font-size:20px; font-weight:700; letter-spacing:.5px; }
.hero .sub { font-size:13px; opacity:.85; margin-top:6px; }
.hero .nw { font-size:42px; font-weight:800; margin:16px 0 4px;
  font-variant-numeric:tabular-nums; letter-spacing:-.5px; }
.hero .nw small { font-size:16px; font-weight:500; opacity:.9; }
.hero .tags { display:flex; gap:14px; flex-wrap:wrap; margin-top:14px; font-size:13px; }
.hero .tags div { background:rgba(255,255,255,.16); padding:5px 12px; border-radius:20px; }
h2 { font-size:15px; font-weight:700; color:#0f172a; margin-bottom:14px;
  padding-left:11px; border-left:4px solid #0e7490; }
.sim { background:#ecfeff; border:1px solid #a5f3fc; border-radius:12px; padding:14px;
  margin-bottom:16px; }
.sim label { font-size:13.5px; color:#155e75; font-weight:600; }
input[type=number], input[type=text] { font-size:14px; padding:6px 10px; border:1px solid #cbd5e1;
  border-radius:8px; font-variant-numeric:tabular-nums; }
.sim input[type=number], .sim input[type=text] { border-color:#67e8f9; color:#0e7490; font-weight:700; }
.sim input[type=range] { width:100%; margin-top:12px; accent-color:#0e7490; }
.sim select { font-size:14px; padding:6px 8px; border:1px solid #67e8f9; border-radius:8px;
  color:#0e7490; font-weight:600; background:#fff; }
.row { margin-top:12px; display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
.hint { font-size:12.5px; color:#0e7490; margin-top:8px; }
.pos-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; }
.pos { border:1px solid #e2e8f0; border-radius:12px; padding:14px; background:#f8fafc; }
.pos .lvl { font-size:12px; color:#64748b; }
.pos .rg { font-size:15px; font-weight:700; color:#0f172a; margin:2px 0 8px; }
.pos .pct { font-size:26px; font-weight:800; color:#0e7490; font-variant-numeric:tabular-nums; }
.pos .pct small { font-size:13px; font-weight:500; color:#475569; }
.pos .lab { font-size:12px; color:#0f766e; background:#ecfdf5; display:inline-block;
  padding:2px 8px; border-radius:10px; margin-top:6px; }
.pos .rank { font-size:12px; color:#64748b; margin-top:6px; }
.bar { height:7px; background:#e2e8f0; border-radius:6px; margin-top:9px; overflow:hidden; }
.bar i { display:block; height:100%; border-radius:6px;
  background:linear-gradient(90deg,#0ea5e9,#0e7490); }
table { width:100%; border-collapse:collapse; font-size:13.5px; }
table th { background:#f1f5f9; text-align:left; padding:8px 10px; color:#334155;
  font-weight:600; border-bottom:1px solid #e2e8f0; }
table td { padding:6px 10px; border-bottom:1px solid #f1f5f9; }
table td.num { text-align:right; font-variant-numeric:tabular-nums; }
table input, table select { width:100%; font-size:13.5px; padding:5px 8px; }
.btn { font-size:13px; padding:6px 14px; border-radius:8px; border:1px solid #0e7490;
  background:#0e7490; color:#fff; cursor:pointer; font-weight:600; }
.btn.ghost { background:#fff; color:#0e7490; }
.btn.warn { background:#fff; color:#b91c1c; border-color:#fca5a5; padding:4px 9px; }
.catrow { display:flex; align-items:center; gap:12px; margin-bottom:10px; font-size:13.5px; }
.catrow .cn { width:96px; color:#334155; flex:none; }
.catrow .cb { flex:1; height:20px; background:#f1f5f9; border-radius:6px; overflow:hidden; }
.catrow .cb i { display:block; height:100%; background:linear-gradient(90deg,#38bdf8,#0f766e);
  border-radius:6px; }
.catrow .cv { width:140px; text-align:right; color:#0f172a; font-weight:600;
  font-variant-numeric:tabular-nums; flex:none; }
.note { font-size:12.5px; color:#64748b; line-height:1.75; }
.note b { color:#334155; }
.src { font-size:12px; color:#94a3b8; line-height:1.7; margin-top:6px; }
.alert { background:#fffbeb; border:1px solid #fde68a; color:#92400e; font-size:12.5px;
  border-radius:10px; padding:12px 14px; line-height:1.7; }
.tot { margin-top:12px; font-size:14px; display:flex; gap:22px; flex-wrap:wrap; }
.tot b { font-variant-numeric:tabular-nums; color:#0f172a; }
.foot { text-align:center; font-size:11.5px; color:#94a3b8; padding:8px 0 20px; }
</style>
</head>
<body>
<div class="wrap">

  <div class="hero">
    <h1>身价罗盘 · 资产估值与分位定位报告</h1>
    <div class="sub">署名：$owner　|　口径：$scope　|　计算时点：$date　|　基准年度：2025</div>
    <div class="nw">¥<span id="nwShow">$networth</span> <small>元 净资产</small></div>
    <div class="tags">
      <div>总资产 ¥<span id="taShow">$total_assets</span></div>
      <div>总负债 ¥<span id="tlShow">$total_liab</span></div>
      <div>资产类别 <span id="ncShow">$ncat</span> 类</div>
    </div>
  </div>

  $editor_card

  $estimate_card

  <div class="card">
    <h2>四级分位定位</h2>
    $interactive_block
    <div class="pos-grid" id="posGrid">$position_cards</div>
  </div>

  <div class="card">
    <h2>资产构成</h2>
    <div id="catBox">$cat_bars</div>
  </div>

  <div class="card">
    <h2>方法与口径说明</h2>
    <div class="note">
      <p><b>1. 分位口径</b>：结果为「净资产 ≥ 本值」的家庭占比（即排在前百分之几）。全国口径以全国家庭净资产中位数约 ¥$median_num 与胡润财富报告高端门槛（600 万 / 1,000 万 / 1 亿元）标定对数正态分布；高于 600 万元的部分改用胡润锚点对数插值。</p>
      <p><b>2. 地区校准</b>：省 / 市 / 县区门槛 = 全国门槛 × 地区系数，系数 = √(居民收入比 × 富裕家庭密度比)。地级市与县区层为代理估算【估】。</p>
      <p><b>3. 排名户数</b>：约前 N 户 = 分位比例 × 该地区家庭户数。</p>
      <p><b>4. 房产估价</b>：小区名匹配内置房价库（$cm_count 条小区 / $dt_count 个地区均价，2025—2026 挂牌参考）；未收录的按所选地区均价估算，均可手动改写。</p>
      <p><b>5. 精度边界</b>：本报告为统计近似定位，非精确排名。中低分位（>10%）可信度较高，前 1% 以内高端区间误差放大，仅作量级参考。</p>
    </div>
    <div class="src">$sources</div>
  </div>

  <div class="card">
    <div class="alert">$disclaimer</div>
  </div>

  <div class="foot">身价罗盘 Net Worth Compass v3.0 · 生成于 $date · 数据口径以公开统计为准</div>
</div>
$js_block
</body>
</html>
"""

EDITOR_BLOCK = """<div class="card">
    <h2>资产录入（可直接修改）</h2>
    <table>
      <thead><tr><th style="width:42%">项目名称</th><th style="width:22%">类别</th>
        <th style="width:26%;text-align:right">金额（元）</th><th style="width:10%"></th></tr></thead>
      <tbody id="assetRows"></tbody>
    </table>
    <div class="row">
      <button class="btn ghost" onclick="addAsset()">+ 添加一项</button>
      <button class="btn ghost" onclick="quickAdd('\u5fae\u4fe1')">+ 微信</button>
      <button class="btn ghost" onclick="quickAdd('\u652f\u4ed8\u5b9d')">+ 支付宝</button>
      <button class="btn ghost" onclick="quickAdd('\u73b0\u91d1\u5b58\u6b3e')">+ 现金存款</button>
      <button class="btn ghost" onclick="quickAdd('\u80a1\u7968')">+ 股票</button>
      <button class="btn ghost" onclick="quickAdd('\u57fa\u91d1')">+ 基金</button>
      <button class="btn ghost" onclick="quickAdd('\u516c\u79ef\u91d1')">+ 公积金</button>
      <label style="font-size:13.5px;color:#334155;">负债合计：</label>
      <input type="number" id="liabInput" value="__LIAB__" step="10000" style="width:170px">
      <span style="font-size:13px;color:#64748b;">元</span>
    </div>
    <div class="tot">
      <span>总资产 <b id="taShow2">—</b></span>
      <span>总负债 <b id="tlShow2">—</b></span>
      <span>净资产 <b id="nwShow2">—</b></span>
    </div>
    <div class="hint" style="color:#64748b;">改动任意金额或名称，上方净资产与下方分位会同步刷新。</div>
  </div>"""

ESTIMATE_BLOCK = """<div class="card">
    <h2>房产估价（输入小区自动估算）</h2>
    <div class="row">
      <input type="text" id="cmName" placeholder="小区名称，如：万科金域东郡" style="min-width:220px;flex:1">
      <input type="number" id="cmArea" placeholder="建筑面积 ㎡" style="width:130px">
      <button class="btn" onclick="doEstimate()">估价</button>
    </div>
    <div class="row">
      <label style="font-size:13.5px;color:#334155;">单价：</label>
      <input type="number" id="cmPrice" placeholder="元/㎡（可手改）" style="width:160px">
      <span style="font-size:13px;color:#64748b;">元/㎡</span>
      <span style="margin-left:auto;font-size:14px;">估值：<b id="cmValue" style="font-size:18px;color:#0e7490;">—</b> 元</span>
      <button class="btn ghost" onclick="fillHome()">填入资产</button>
    </div>
    <div class="hint" id="cmHint" style="color:#0e7490;">输入小区名与面积，点「估价」自动匹配参考单价</div>
  </div>"""

INTERACTIVE_BLOCK = """<div class="sim">
      <label>当前净资产：</label>
      <input type="number" id="nvInput" value="__NV__" step="10000" min="0">
      <span style="font-size:13px;color:#155e75;">元</span>
      <input type="range" id="nvRange" min="0" max="20000000" step="50000" value="__NV__">
      <div class="row">
        <label>地区：</label>
        <select id="selProv"></select>
        <select id="selCity"></select>
        <select id="selCounty"></select>
      </div>
      <div class="hint">拖动滑块或改金额，切换省 / 市 / 区县 —— 分位即时刷新</div>
    </div>"""

JS_BLOCK = r"""<script>
const MODEL = __MODEL__;
const HOUSING = __HOUSING__;
const ALL = MODEL.regions;
const NAT = MODEL.national;
const DEF = MODEL.default;
const CATS = ["\u623f\u4ea7","\u8f66\u8f86","\u73b0\u91d1\u5b58\u6b3e","\u7406\u8d22\u6295\u8d44","\u516c\u79ef\u91d1","\u80a1\u6743\u51fa\u8d44","\u5e94\u6536\u501f\u51fa","\u5176\u4ed6\u8d44\u4ea7"];
let ASSETS = __ASSETS__;
let LIAB = __LIAB__;

function erf(x){const s=x<0?-1:1;x=Math.abs(x);const a1=0.254829592,a2=-0.284496736,a3=1.421413741,a4=-1.453152027,a5=1.061405429,p=0.3275911;const t=1/(1+p*x);return s*(1-((((a5*t+a4)*t+a3)*t+a2)*t+a1)*t*Math.exp(-x*x));}
function normCdf(x){return 0.5*(1+erf(x/Math.SQRT2));}
function pctNat(x){const med=MODEL.median,sg=MODEL.sigma;const A=MODEL.anchors.slice().sort(function(a,b){return a.t-b.t;});if(x<=0)return 99.0;if(x<A[0].t){const z=(Math.log(x)-Math.log(med))/sg;return Math.max(0.0001,Math.min(99.99,100*(1-normCdf(z))));}const pts=A.map(function(a){return [Math.log(a.t),Math.log(a.p)];});const lx=Math.log(x);if(lx>=pts[pts.length-1][0]){const p0=pts[pts.length-2],p1=pts[pts.length-1];const k=(p1[1]-p0[1])/(p1[0]-p0[0]);return Math.exp(p1[1]+k*(lx-p1[0]));}for(let i=0;i<pts.length-1;i++){if(lx>=pts[i][0]&&lx<=pts[i+1][0]){const t=(lx-pts[i][0])/(pts[i+1][0]-pts[i][0]);return Math.exp(pts[i][1]+t*(pts[i+1][1]-pts[i][1]));}}return Math.exp(pts[0][1]);}
function pctOf(nv,coef){return pctNat(nv/(coef||1));}
function lab(p){if(p<=0.05)return "\u5168\u56fd\u9876\u5c16 \u00b7 \u524d 0.05%";if(p<=0.1)return "\u524d 0.1% \u00b7 \u8d85\u9ad8\u51c0\u503c";if(p<=0.5)return "\u524d 0.5%";if(p<=1)return "\u524d 1% \u00b7 \u5bcc\u88d5\u5bb6\u5ead";if(p<=5)return "\u524d 5% \u00b7 \u9ad8\u6536\u5165";if(p<=10)return "\u524d 10% \u00b7 \u4e2d\u4e0a";if(p<=25)return "\u524d 25% \u00b7 \u4e2d\u4e0a";if(p<=50)return "\u524d 50% \u00b7 \u4e2d\u4f4d\u4ee5\u4e0a";return "\u540e 50%";}
function fmt(n){return Math.round(n).toLocaleString('en-US');}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');}

function classify(n){
  n=String(n||"");
  const rules=[["\u516c\u79ef\u91d1",["\u516c\u79ef\u91d1"]],["\u623f\u4ea7",["\u623f","\u5b85","\u522b\u5885","\u516c\u5bd3","\u5546\u94fa","\u5199\u5b57\u697c","\u4e0d\u52a8\u4ea7","\u8f66\u4f4d"]],["\u8f66\u8f86",["\u6c7d\u8f66","\u8f7f\u8f66","\u8f66","\u6469\u6258"]],["\u80a1\u6743\u51fa\u8d44",["\u80a1\u6743","\u80a1\u4efd","\u51fa\u8d44","\u6ce8\u518c\u8d44\u672c"]],["\u5e94\u6536\u501f\u51fa",["\u5e94\u6536","\u501f\u51fa","\u6b20\u6b3e","\u503a\u6743","\u62bc\u91d1"]],["\u7406\u8d22\u6295\u8d44",["\u7406\u8d22","\u57fa\u91d1","\u80a1\u7968","\u503a\u5238","\u8bc1\u5238","\u4fe1\u6258","\u4fdd\u9669","\u9ec4\u91d1","\u6295\u8d44","\u56fd\u503a"]],["\u73b0\u91d1\u5b58\u6b3e",["\u5b58\u6b3e","\u6d3b\u671f","\u5b9a\u671f","\u73b0\u91d1","\u94f6\u884c","\u50a8\u84c4","\u652f\u4ed8\u5b9d","\u5fae\u4fe1","\u4f59\u989d"]]];
  for(let i=0;i<rules.length;i++){for(let j=0;j<rules[i][1].length;j++){if(n.indexOf(rules[i][1][j])>=0)return rules[i][0];}}
  return "\u5176\u4ed6\u8d44\u4ea7";
}
function totalAssets(){let s=0;ASSETS.forEach(function(a){s+=(+a.value||0);});return s;}
function netWorth(){return totalAssets()-LIAB;}

function renderAssets(){
  let h='';
  ASSETS.forEach(function(a,i){
    let opts=CATS.map(function(c){return '<option'+(c===a.cat?' selected':'')+'>'+c+'</option>';}).join('');
    h+='<tr>'
      +'<td><input type="text" value="'+esc(a.name)+'" oninput="upd('+i+',\'name\',this.value)"></td>'
      +'<td><select onchange="upd('+i+',\'cat\',this.value)">'+opts+'</select></td>'
      +'<td><input type="number" value="'+(a.value||0)+'" oninput="upd('+i+',\'value\',this.value)"></td>'
      +'<td><button class="btn warn" onclick="delAsset('+i+')">删除</button></td>'
      +'</tr>';
  });
  document.getElementById('assetRows').innerHTML=h;
}
function upd(i,f,v){ASSETS[i][f]=(f==='value'?(+v||0):v);refresh();}
function addAsset(){ASSETS.push({name:'',cat:'\u5176\u4ed6\u8d44\u4ea7',value:0});renderAssets();refresh();}
function quickAdd(n){ASSETS.push({name:n,cat:classify(n),value:0});renderAssets();refresh();}
function delAsset(i){ASSETS.splice(i,1);renderAssets();refresh();}
function setLiab(v){LIAB=(+v||0);refresh();}

function renderCats(){
  const by={};const tot=totalAssets();
  ASSETS.forEach(function(a){by[a.cat]=(by[a.cat]||0)+(+a.value||0);});
  const keys=Object.keys(by).sort(function(x,y){return by[y]-by[x];});
  if(!keys.length){document.getElementById('catBox').innerHTML='<div class="note">\u65e0\u8d44\u4ea7\u6570\u636e</div>';return;}
  let h='';
  keys.forEach(function(k){
    const pct=tot?(by[k]/tot*100):0;
    h+='<div class="catrow"><div class="cn">'+k+'</div>'
      +'<div class="cb"><i style="width:'+pct.toFixed(1)+'%"></i></div>'
      +'<div class="cv">\u00a5'+fmt(by[k])+'\u3000'+pct.toFixed(1)+'%</div></div>';
  });
  document.getElementById('catBox').innerHTML=h;
}
function byCode(c){for(let i=0;i<ALL.length;i++){if(ALL[i].code===c)return ALL[i];}return null;}
function nameOf(c){const r=byCode(c);return r?r.name:c;}
function fill(selId,items,defVal){
  const sel=document.getElementById(selId);
  let s='<option value="">\uff08\u4e0d\u9650\uff09</option>';
  items.forEach(function(r){s+='<option value="'+r.code+'">'+r.name+'</option>';});
  sel.innerHTML=s;
  sel.value=(defVal&&items.some(function(r){return r.code===defVal;}))?defVal:'';
}
function citiesOf(pc){return ALL.filter(function(r){return r.level==='\u5e02'&&r.code.slice(0,2)===pc.slice(0,2);});}
function countiesOf(cc){return ALL.filter(function(r){return r.level==='\u53bf\u533a'&&r.code.slice(0,4)===cc.slice(0,4);});}
function countiesOfProv(pc){return ALL.filter(function(r){return r.level==='\u53bf\u533a'&&r.code.slice(0,2)===pc.slice(0,2);});}
function syncCounties(){
  const pc=document.getElementById('selProv').value;
  const cc=document.getElementById('selCity').value;
  if(cc){fill('selCounty',countiesOf(cc),'');}
  else if(pc){fill('selCounty',countiesOfProv(pc),'');}
  else{fill('selCounty',[],'');}
}
function onProv(){const pc=document.getElementById('selProv').value;
  fill('selCity',pc?citiesOf(pc):ALL.filter(function(r){return r.level==='\u5e02';}),'');syncCounties();render();}
function onCity(){syncCounties();render();}
function chain(){
  const list=[NAT];
  const pc=document.getElementById('selProv').value, cc=document.getElementById('selCity').value, yc=document.getElementById('selCounty').value;
  if(pc){const r=byCode(pc);if(r)list.push(r);}
  if(cc){const r=byCode(cc);if(r)list.push(r);}
  if(yc){const r=byCode(yc);if(r)list.push(r);}
  return list;
}
function render(){
  const nw=netWorth();
  const inp=document.getElementById('nvInput');
  if(document.activeElement!==inp){inp.value=Math.round(nw);}
  const nv=parseFloat(inp.value)||0;
  document.getElementById('nvRange').value=Math.min(Math.max(nv,0),20000000);
  let out='';
  chain().forEach(function(r){
    const p=pctOf(nv,r.coef);
    const w=Math.max(1.2,Math.min(100,p));
    out+='<div class="pos"><div class="lvl">'+r.level+'</div>'
      +'<div class="rg">'+r.name+'</div>'
      +'<div class="pct">\u524d '+p.toFixed(2)+'<small>%</small></div>'
      +'<div class="lab">'+lab(p)+'</div>'
      +'<div class="bar"><i style="width:'+w.toFixed(1)+'%"></i></div>'
      +'<div class="rank">\u7ea6\u524d '+fmt(p/100*r.households)+' \u6237 / \u5171 '+fmt(r.households)+' \u6237</div></div>';
  });
  document.getElementById('posGrid').innerHTML=out;
  document.getElementById('nwShow').textContent=fmt(nw);
  document.getElementById('taShow').textContent=fmt(totalAssets());
  document.getElementById('tlShow').textContent=fmt(LIAB);
  if(document.getElementById('taShow2')){
    document.getElementById('taShow2').textContent='\u00a5'+fmt(totalAssets());
    document.getElementById('tlShow2').textContent='\u00a5'+fmt(LIAB);
    document.getElementById('nwShow2').textContent='\u00a5'+fmt(nv);
  }
  renderCats();
}
function refresh(){render();}

function lookup(name){
  const n=String(name||'').trim();
  if(!n)return null;
  for(let i=0;i<HOUSING.communities.length;i++){if(HOUSING.communities[i].name===n)return HOUSING.communities[i];}
  const cands=HOUSING.communities.filter(function(c){return c.name.indexOf(n)>=0||n.indexOf(c.name)>=0;});
  if(!cands.length)return null;
  cands.sort(function(a,b){return a.name.length-b.name.length;});
  return cands[0];
}
let CMVAL=0;
function doEstimate(){
  const nm=document.getElementById('cmName').value.trim();
  const area=parseFloat(document.getElementById('cmArea').value)||0;
  let price=parseFloat(document.getElementById('cmPrice').value)||0;
  let hint='';
  if(!price){
    const hit=lookup(nm);
    if(hit){price=hit.price;hint='\u547d\u4e2d\u5c0f\u533a\u5e93\uff1a'+hit.name+'\uff08'+hit.district+'\uff09\u53c2\u8003\u5355\u4ef7 '+fmt(price)+' \u5143/\u33a1';}
    else{
      const code=document.getElementById('selCounty').value||document.getElementById('selCity').value||document.getElementById('selProv').value;
      if(code&&HOUSING.districts[code]){price=HOUSING.districts[code];hint='\u672a\u6536\u5f55\u8be5\u5c0f\u533a\uff0c\u6309\u3010'+nameOf(code)+'\u3011\u5747\u4ef7 '+fmt(price)+' \u5143/\u33a1 \u4f30\u7b97';}
      else{hint='\u672a\u6536\u5f55\uff0c\u8bf7\u624b\u52a8\u586b\u5199\u5355\u4ef7';}
    }
    document.getElementById('cmPrice').value=price||'';
  } else { hint='\u6309\u624b\u586b\u5355\u4ef7\u8ba1\u7b97'; }
  const val=area*price;
  CMVAL=val;
  document.getElementById('cmValue').textContent=val?fmt(val):'\u2014';
  document.getElementById('cmHint').textContent=hint;
}
function fillHome(){
  if(!CMVAL){alert('\u8bf7\u5148\u70b9\u300c\u4f30\u4ef7\u300d');return;}
  const nm=document.getElementById('cmName').value.trim()||'\u623f\u4ea7';
  const area=parseFloat(document.getElementById('cmArea').value)||0;
  ASSETS.push({name:nm+(area?'\uff08'+area+'\u33a1\uff09':''),cat:'\u623f\u4ea7',value:Math.round(CMVAL)});
  renderAssets();render();
  document.getElementById('cmHint').textContent='\u5df2\u586b\u5165\u8d44\u4ea7\u8868\uff1a'+nm+' \u00a5'+fmt(CMVAL);
}
function init(){
  fill('selProv',ALL.filter(function(r){return r.level==='\u7701';}),DEF.prov||'');
  fill('selCity',DEF.prov?citiesOf(DEF.prov):ALL.filter(function(r){return r.level==='\u5e02';}),DEF.city||'');
  fill('selCounty',DEF.city?countiesOf(DEF.city):[],DEF.county||'');
  document.getElementById('selProv').addEventListener('change',onProv);
  document.getElementById('selCity').addEventListener('change',onCity);
  document.getElementById('selCounty').addEventListener('change',render);
  document.getElementById('nvInput').addEventListener('input',function(){
    document.getElementById('nvRange').value=Math.min(this.value,20000000);
    render();
  });
  document.getElementById('nvRange').addEventListener('input',function(e){
    document.getElementById('nvInput').value=e.target.value;
  });
  if(document.getElementById('liabInput')){
    document.getElementById('liabInput').addEventListener('input',function(){setLiab(this.value);});
  }
  renderAssets();
  render();
}
init();
</script>"""


def fmt(n):
    return f"{n:,.0f}"


def build_cards(positions):
    out = []
    for p in positions:
        width = min(100.0, max(1.2, p["top_pct"]))
        out.append(f"""<div class="pos">
      <div class="lvl">{html.escape(p['level'])}</div>
      <div class="rg">{html.escape(p['region'])}</div>
      <div class="pct">前 {p['top_pct']:.2f}<small>%</small></div>
      <div class="lab">{html.escape(p['label'])}</div>
      <div class="bar"><i style="width:{width:.1f}%"></i></div>
      <div class="rank">约前 {fmt(p['rank_households'])} 户 / 共 {fmt(p['households'])} 户</div>
    </div>""")
    return "\n".join(out)


def build_cat_bars(by_cat, total):
    if not by_cat:
        return '<div class="note">无资产数据</div>'
    rows = []
    for cat, val in sorted(by_cat.items(), key=lambda x: -x[1]):
        pct = (val / total * 100) if total else 0
        rows.append(f"""<div class="catrow">
      <div class="cn">{html.escape(cat)}</div>
      <div class="cb"><i style="width:{pct:.1f}%"></i></div>
      <div class="cv">¥{fmt(val)}　{pct:.1f}%</div>
    </div>""")
    return "\n".join(rows)


def build_js(result):
    with open(BASELINE_PATH, "r", encoding="utf-8") as f:
        bl = json.load(f)
    with open(HOUSING_PATH, "r", encoding="utf-8") as f:
        hs = json.load(f)
    regions = [{"code": c, "name": r["name"], "level": r.get("level", "县区"),
                "households": r["households"], "coef": r["coef"]}
               for c, r in bl["regions"].items()]
    nat = bl["national"]
    rc = str(result["meta"].get("region_code", "") or "")
    default = {"prov": (rc[:2] + "0000") if len(rc) == 6 else "",
               "city": (rc[:4] + "00") if len(rc) == 6 else "",
               "county": rc if rc in bl["regions"] else ""}
    model = {
        "median": result["model"]["median_national"],
        "sigma": result["model"]["sigma"],
        "anchors": [{"t": a["threshold"], "p": a["top_pct"]} for a in nat["anchors"]],
        "regions": regions,
        "national": {"code": "CN", "name": "全国", "level": "全国",
                     "households": nat["households"], "coef": 1.0},
        "default": default,
    }
    assets = [{"name": it["name"], "cat": cat, "value": it["value"]}
              for cat, items in result["summary"]["detail"].items() for it in items]
    js = (JS_BLOCK
          .replace("__MODEL__", json.dumps(model, ensure_ascii=False))
          .replace("__HOUSING__", json.dumps(hs, ensure_ascii=False))
          .replace("__ASSETS__", json.dumps(assets, ensure_ascii=False))
          .replace("__LIAB__", str(result["summary"]["total_liabilities"])))
    return js


def build_md(r, hs, title):
    """把测算结果转成 Markdown 底稿，供基座渲染（静态版）。"""
    s = r["summary"]
    m = r["meta"]
    nv = s["net_worth"]
    ta = s["total_assets"]
    tl = s["total_liabilities"]
    L = []
    L.append("# %s" % title)
    L.append("")
    L.append("本页由 HTML 基座渲染生成，具备顶部胶囊目录、章节滚动联动与内容动效，可直接打印或归档。"
             "测算范围为 %s，生成日期 %s。三项核心结果与逐项明细均来自输入清单归集，"
             "分类构成与分位定位分别在下文对应章节展开。"
             % (m.get("scope", ""), m.get("generated", "")))
    L.append("")

    L.append("## 一、净资产总览")
    L.append("")
    L.append("净资产等于资产合计扣除负债合计，是衡量家庭财务位置的主指标。资产合计反映可计入的存量财富规模，"
             "负债合计反映尚未清偿的债务余额，两者差额即净资产。类别数反映资产归集的口径宽度，"
             "口径越宽越能反映真实家底，口径过窄则容易高估或低估位置。三项数据逐项可在第四节明细表中核对，"
             "任一项目的增减都会同步反映到本节结果。为便于对照，建议先按类别汇总核对总额，再逐项核对细目；前者看结构是否合理，后者看录入是否准确。若发现总额与预期不符，多半是某一项归类或金额有偏差，回到明细表逐项复核即可定位。总览项同时是分位定位的计算基数，数值准确是后续判断成立的前提。")
    L.append("")
    L.append(":::kpi")
    L.append("净资产|%s|元|资产减负债" % fmt(nv))
    L.append("资产合计|%s|元|可计入资产" % fmt(ta))
    L.append("负债合计|%s|元|待清偿债务" % fmt(tl))
    L.append("资产类别|%d|类|归集口径" % len(s["by_category"]))
    L.append(":::")
    L.append("")

    L.append("## 二、资产构成")
    L.append("")
    L.append("资产构成按类别归集后展示占比。占比高的一类通常是家庭财富的主要载体，"
             "其流动性、保值性与变现周期直接决定财务安排的空间；占比分散说明资产配置相对均衡，"
             "单一类别波动对总体的冲击较小。判读时结合类别属性看：不动产占比过高会影响短期流动性，"
             "权益类占比过高会放大净值波动，存款类占比过高则收益偏低，长期看会被通胀侵蚀。判断结构是否合适，要看家庭所处阶段与近期资金安排，有购房、教育、医疗等大额支出预期的，流动性权重应更高；支出压力较小的，可适度提高长期资产比重。结构没有统一标准，匹配自身节奏才有效。")
    L.append("")
    if s["by_category"]:
        L.append(":::bar")
        for cat, val in sorted(s["by_category"].items(), key=lambda x: -x[1]):
            pct = (val / ta * 100) if ta else 0
            L.append("%s|%.1f%%|%s 元" % (cat, pct, fmt(val)))
        L.append(":::")
    else:
        L.append("本次输入未含分类资产数据，构成分析从略。")
    L.append("")

    L.append("## 三、财富分位定位")
    L.append("")
    L.append("分位定位把净资产放进对应层级的家庭分布中比较，给出排在全体家庭前百分之几的估算位置。"
             "层级自全国向下细到省、市、县区，层级越细参照样本越贴近本地实际，位置也越具可比性。"
             "口径上以各层级家庭户数与分布系数为参照，结果属于统计近似的估算，用于把握大概位置，"
             "不构成任何形式的排名证明。同一净资产在不同层级下的位置可能相差明显，层级越细越贴近本地实际，全国口径适合看整体位置，省与县区口径适合看身边位置。参照数据存在时点差异，若近期资产或负债有较大变动，位置也会随之移动，建议以当期口径为准。")
    L.append("")
    L.append("| 层级 | 参照范围 | 估算位置 | 参照户数 |")
    L.append("|---|---|---|---|")
    for p in r.get("positions", []):
        L.append("| %s | %s | 前 %.2f%% | 约 %s 户 |" % (
            p.get("level", ""), p.get("region", ""), p.get("top_pct", 0),
            fmt(p.get("households", 0))))
    L.append("")

    L.append("## 四、资产明细")
    L.append("")
    L.append("明细表逐项列出归集到的资产，按类别分组。核对时先看金额是否与原始凭据一致，"
             "再看类别归属是否恰当；同一项目被重复计入会抬高净资产，遗漏则会低估位置。"
             "负债项在总览中已扣减，本表仅列资产侧明细。核对时还应留意口径一致性：同一资产不要在多个类别下重复登记，共有资产按约定份额计入，估值类资产以最近一次可核实的市值为准。明细越完整，分位结果越可靠。")
    L.append("")
    L.append("| 项目 | 类别 | 金额（元） |")
    L.append("|---|---|---|")
    for cat, items in s["detail"].items():
        for it in items:
            L.append("| %s | %s | %s |" % (
                str(it["name"]).replace("|", "/"), cat, fmt(it["value"])))
    L.append("")

    L.append("## 五、说明与来源")
    L.append("")
    L.append("估价口径与数据来源如下，用于核对与追溯。房产估价依据小区与区县两个层级的房价库匹配，"
             "未命中时按区县均值估算；其余资产按输入清单原值计入。结果属于统计近似，"
             "受参照数据时点与覆盖范围影响，供个人盘点和沟通参考。由于参照数据覆盖范围与更新时点存在差异，估算结果可能与实际统计口径不完全一致，使用时宜作为区间参考而非精确结论。若用于对外沟通，建议同时说明估算方法、参照层级与数据时点，以便对方理解结果的适用范围与限度。")
    L.append("")
    src = "；".join(x for x in r.get("sources", []) if x)
    if src:
        L.append("数据来源：%s。" % src)
        L.append("")
    L.append("> %s" % r.get("disclaimer", ""))
    L.append("")

    L.append("## 六、结论")
    L.append("")
    L.append("综合看，本次归集得到 %d 类资产，资产合计 %s 元，负债合计 %s 元，净资产 %s 元。"
             % (len(s["by_category"]), fmt(ta), fmt(tl), fmt(nv)))
    L.append("")
    L.append("分位定位给出的位置可用于横向参照，判断财务安排的空间与优先级。"
             "在此基础上，调整资产结构、控制负债水平、提升流动性，都是可操作的着力点。"
             "本页由基座一次渲染产出，目录、动效与打印版式随页面一并就绪，可直接分发或归档留档。"
             "相较旧模板，本版新增顶部胶囊目录、章节滚动联动与内容错峰淡入，长报告翻阅与定位更省力；"
             "打印时自动还原为静态排版，不影响纸质输出效果。"
             "如需互动推演，使用 --interactive 参数生成互动版即可。互动版支持资产增删改、房产按小区估价与地区切换，适合边聊边算；静态版适合打印、归档与正式分发。两种版本的口径一致，结果可以互相印证，可按场景各取所需，日常盘点用静态版即可，需现场调整数据时再切互动版。")
    L.append("")
    return "\n".join(L)


def render_base(md, out, title, hero):
    """调用内嵌 HTML 基座渲染；成功返回 True，失败返回 False（由调用方回落旧模板）。"""
    import subprocess
    import sys
    import tempfile
    base = os.path.join(BASE_DIR, "scripts", "htmlbase", "md2report.py")
    if not os.path.exists(base):
        return False
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tf:
            tf.write(md)
            tmp = tf.name
        cmd = [sys.executable, base, tmp, "-o", out,
               "--title", title,
               "--theme", "galaxy", "--motif", "narrative",
               "--hero-stats", hero, "--hero-badge", "身价罗盘", "--check"]
        rr = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if rr.stdout:
            for ln in rr.stdout.strip().splitlines()[-4:]:
                print("  [基座]", ln)
        return os.path.exists(out)
    except Exception as e:
        print("  [基座] 渲染失败，回落旧模板：%r" % e)
        return False
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)


def main():
    ap = argparse.ArgumentParser(description="身价罗盘 · HTML 报告生成器 v3.0")
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="nwc_report.html")
    ap.add_argument("--interactive", action="store_true")
    ap.add_argument("--no-base", action="store_true", help="强制使用旧模板")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        r = json.load(f)
    with open(HOUSING_PATH, "r", encoding="utf-8") as f:
        hs = json.load(f)
    s = r["summary"]
    m = r["meta"]
    nv = s["net_worth"]

    ib, jb, ec, est = "", "", "", ""
    if args.interactive:
        ib = INTERACTIVE_BLOCK.replace("__NV__", str(int(nv)))
        jb = build_js(r)
        ec = EDITOR_BLOCK.replace("__LIAB__", str(int(s["total_liabilities"])))
        est = ESTIMATE_BLOCK

    # 静态版：保留明细表
    if not args.interactive:
        rows = "".join(
            f"<tr><td>{html.escape(it['name'])}</td><td>{html.escape(cat)}</td>"
            f"<td class='num'>{fmt(it['value'])}</td></tr>"
            for cat, items in s["detail"].items() for it in items)
        ec = ('<div class="card"><h2>资产明细</h2><table>'
              '<thead><tr><th>项目</th><th>类别</th><th style="text-align:right">金额（元）</th></tr></thead>'
              f'<tbody>{rows}</tbody></table></div>')

    if not args.interactive and not args.no_base:
        _hero = "%s|净资产" % fmt(nv)
        if r.get("positions"):
            _hero += " ;; 前 %.2f%%|全国分位" % r["positions"][0]["top_pct"]
        if render_base(build_md(r, hs, "身价罗盘 · %s" % m["owner"]), args.out,
                       "身价罗盘 · %s" % m["owner"], _hero):
            print(f"HTML 报告已生成（HTML 基座）：{args.out}")
            return

    out = Template(TEMPLATE).safe_substitute(
        title=f"身价罗盘 · {m['owner']}",
        owner=html.escape(m["owner"]),
        scope=html.escape(m["scope"]),
        date=m["generated"],
        networth=fmt(nv),
        total_assets=fmt(s["total_assets"]),
        total_liab=fmt(s["total_liabilities"]),
        ncat=len(s["by_category"]),
        position_cards=build_cards(r["positions"]),
        cat_bars=build_cat_bars(s["by_category"], s["total_assets"]),
        median_num=fmt(r["model"]["median_national"]),
        cm_count=len(hs["communities"]),
        dt_count=len(hs["districts"]),
        sources="数据来源：" + "；".join(html.escape(x) for x in r["sources"] if x) + "。",
        disclaimer=html.escape(r["disclaimer"]),
        interactive_block=ib,
        js_block=jb,
        editor_card=ec,
        estimate_card=est,
    )
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"HTML 报告已生成：{args.out}（{'互动推演版' if args.interactive else '静态版'}）")


if __name__ == "__main__":
    main()
