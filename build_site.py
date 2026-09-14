#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建静态站点：题库内嵌为 data.js，页面按日期自动算出当天 5 题。

同时输出到两处：
  site/  —— 供 WorkBuddy 发布（本地链路）
  docs/  —— 供 GitHub Pages 发布（云端链路，无需本机在线）

发布一次即可，链接固定；以后只需更新题库后重新构建并提交。
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(BASE, "题库.json")
SITE = os.path.join(BASE, "site")
DOCS = os.path.join(BASE, "docs")
START_DATE = "2026-09-14"
PER_DAY = 5

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="referrer" content="no-referrer">
<title>专业一·名词解释每日五题</title>
<style>
:root{--bg:#f7f6f3;--card:#fff;--line:#e5e2dc;--ink:#1f1e1c;--ink2:#5f5e5a;--ink3:#8a8880;--accent:#a32d2d;--accent-bg:#fcebeb;--ok:#3b6d11;--ok-bg:#eaf3de}
*{box-sizing:border-box}
body{margin:0;padding:16px 14px 48px;background:var(--bg);color:var(--ink);font:15px/1.65 system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;-webkit-text-size-adjust:100%}
.wrap{max-width:680px;margin:0 auto}
h1{font-size:19px;font-weight:600;margin:0 0 5px}
.sub{font-size:13px;color:var(--ink2)}
.tip{margin-top:12px;padding:10px 12px;background:#fff8e6;border:1px solid #f0dfb8;border-radius:10px;font-size:13px;color:#7a5b0b}
.bar{display:flex;gap:8px;margin:16px 0 2px}
.bar button{flex:1;padding:9px 0;font-size:13px;border:1px solid var(--line);background:var(--card);color:var(--ink2);border-radius:9px;cursor:pointer}
.bar button:active{background:#f1efe8}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:12px 0;overflow:hidden}
.q{padding:14px 15px;display:flex;gap:11px;align-items:flex-start;cursor:pointer;list-style:none}
.q::-webkit-details-marker{display:none}
.q:active{background:#faf9f6}
.no{flex:0 0 26px;height:26px;border-radius:8px;background:var(--ink);color:#fff;font-size:13px;display:flex;align-items:center;justify-content:center;margin-top:1px}
.qmain{flex:1;min-width:0}
.term{font-size:16px;font-weight:600}
.meta{margin-top:5px;display:flex;flex-wrap:wrap;gap:6px}
.tag{font-size:11px;padding:2px 7px;border-radius:5px;background:#f1efe8;color:var(--ink2)}
.tag.hot{background:var(--accent-bg);color:var(--accent);font-weight:500}
.hint{font-size:12px;color:var(--ink3);margin-top:6px}
.a{padding:0 15px 15px 52px;border-top:1px dashed var(--line)}
.a h4{margin:14px 0 6px;font-size:13px;color:var(--ink2);font-weight:600}
.def{font-size:14.5px;margin:0}
ol{margin:0;padding-left:20px}ol li{font-size:14px;margin:5px 0}
.mn{background:var(--ok-bg);border-radius:8px;padding:9px 11px;font-size:13.5px;color:#27500a}
.src{font-size:11.5px;color:var(--ink3);margin-top:10px;line-height:1.6}
.nav{display:flex;justify-content:space-between;gap:10px;margin-top:22px}
.nav a{flex:1;text-align:center;padding:10px 0;font-size:13px;color:var(--ink2);text-decoration:none;border:1px solid var(--line);border-radius:9px;background:var(--card)}
footer{margin-top:24px;font-size:11.5px;color:var(--ink3);text-align:center;line-height:1.7}
</style>
</head>
<body>
<div class="wrap">
<h1 id="h1">加载中</h1>
<div class="sub" id="sub"></div>
<div class="tip">先自己在心里答一遍，再点题目展开答案。答不出的记下来，当天背熟。</div>
<div class="bar"><button onclick="allOpen(true)">全部展开</button><button onclick="allOpen(false)">全部收起</button></div>
<div id="list"></div>
<div class="nav"><a id="prev" href="#">&#8592; 前一天</a><a id="next" href="#">后一天 &#8594;</a></div>
<footer id="foot"></footer>
</div>
<script src="data.js"></script>
<script>
var START = "__START__", PER = __PER__, TOTAL = 0;
function pad(n){return n<10?'0'+n:''+n}
function iso(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate())}
function parse(s){var p=s.split('-');return new Date(+p[0],+p[1]-1,+p[2])}
function shift(s,n){var d=parse(s);d.setDate(d.getDate()+n);return iso(d)}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function itemsFor(day){
  var n = Math.round((parse(day)-parse(START))/86400000);
  var nz=ZQ.length, nb=BC.length, perB=PER-1;
  var z=ZQ[((n%nz)+nz)%nz];
  var bs=((n*perB)%nb+nb)%nb;
  var out=[], bi=0, mid=Math.floor(perB/2);
  for(var i=0;i<perB;i++){
    if(i===mid){out.push(z)}
    out.push(BC[(bs+bi)%nb]); bi++;
  }
  if(mid>=perB){out.push(z)}
  return {items:out, round: Math.floor(n/nz)+1, idx:n+1};
}
function render(day){
  var r = itemsFor(day), h='';
  document.getElementById('h1').textContent = day + ' · 专业一名词解释 ' + PER + ' 题';
  document.getElementById('sub').textContent = '北京电影学院 艺术基础理论 · 第 ' + r.idx + ' 期（第 ' + r.round + ' 轮 · 真题 ' + ZQ.length + ' + 补充 ' + BC.length + '）';
  r.items.forEach(function(it,i){
    var tags='';
    if(it.track==='真题'){tags+='<span class="tag hot">真题</span>'}
    (it.years||[]).forEach(function(y){tags+='<span class="tag hot">'+esc(y)+'</span>'});
    if(it.origin==='真题隐含'){tags+='<span class="tag hot">真题衍生</span>'}
    (it.tags||[]).forEach(function(t){tags+='<span class="tag">'+esc(t)+'</span>'});
    var pts='';(it.points||[]).forEach(function(p){pts+='<li>'+esc(p)+'</li>'});
    h+='<details class="card" data-i="'+i+'"><summary class="q"><span class="no">'+(i+1)+
       '</span><span class="qmain"><span class="term">'+esc(it.term)+
       '</span><span class="meta">'+tags+'</span><span class="hint">点一下展开答案</span></span></summary>'+
       '<div class="a"><h4>定义</h4><p class="def">'+esc(it.definition)+'</p>'+
       '<h4>答题要点</h4><ol>'+pts+'</ol>'+
       '<h4>记忆锚点</h4><div class="mn">'+esc(it.mnemonic)+'</div>'+
       '<div class="src">'+esc(it.source_note)+'</div></div></details>';
  });
  document.getElementById('list').innerHTML=h;
  document.getElementById('prev').href='?d='+shift(day,-1);
  document.getElementById('next').href='?d='+shift(day,1);
  document.getElementById('foot').innerHTML='每期 1 道真题 + 4 道补充，真题 29 条与补充 116 条同为 29 天一轮，一轮内不重复。条目标注的页码为彭吉象《艺术学概论》第6版／钟大丰舒晓鸣《中国电影史》／郑亚玲胡滨《外国电影史》的核对出处。';
}
function allOpen(v){document.querySelectorAll('details').forEach(function(d){d.open=v})}
var q=new URLSearchParams(location.search).get('d');
var day=(q&&/^\\d{4}-\\d{2}-\\d{2}$/.test(q))?q:iso(new Date());
render(day);
</script>
</body>
</html>"""


def slim_one(it):
    return {
        "term": it["term"],
        "definition": it["definition"],
        "points": it["points"],
        "mnemonic": it["mnemonic"],
        "source_note": it["source_note"],
        "years": it.get("years", []),
        "tags": it.get("tags", []),
        "track": it.get("track", "补充"),
        "origin": it.get("origin", ""),
    }


def main():
    bank = json.load(open(BANK, encoding="utf-8"))
    zhenti = sorted([i for i in bank["items"] if i.get("track") == "真题"],
                    key=lambda x: x.get("zhenti_pos", 10**9))
    buchong = sorted([i for i in bank["items"] if i.get("track") != "真题"],
                     key=lambda x: x.get("buchong_pos", 10**9))
    if not zhenti:
        # 兼容未打轨道的旧题库
        buchong = sorted(bank["items"], key=lambda x: x.get("seq", 10**9))
    zq = [slim_one(i) for i in zhenti]
    bc = [slim_one(i) for i in buchong]

    data = ("var ZQ=" + json.dumps(zq, ensure_ascii=False) + ";\n"
            "var BC=" + json.dumps(bc, ensure_ascii=False) + ";")
    page = HTML.replace("__START__", START_DATE).replace("__PER__", str(PER_DAY))
    for out_dir in (SITE, DOCS):
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "data.js"), "w", encoding="utf-8") as f:
            f.write(data)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
    print("已生成 site/ 与 docs/：index.html + data.js（真题 %d 条 / 补充 %d 条）" % (len(zq), len(bc)))


if __name__ == "__main__":
    main()
