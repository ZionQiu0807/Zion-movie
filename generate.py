#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日名词解释：选题 -> 生成答题页 HTML -> 登记已出题目

用法:
  python generate.py                # 生成今天的页面并登记
  python generate.py --dry-run      # 只看会抽到哪些题，不写文件
  python generate.py --date 2026-09-15
"""
import argparse
import datetime
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(BASE, "题库.json")
PAGES = os.path.join(BASE, "pages")
PER_DAY = 5

TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<style>
:root{{--bg:#f7f6f3;--card:#ffffff;--line:#e5e2dc;--ink:#1f1e1c;--ink2:#5f5e5a;--ink3:#8a8880;--accent:#a32d2d;--accent-bg:#fcebeb;--ok:#3b6d11;--ok-bg:#eaf3de}}
*{{box-sizing:border-box}}
body{{margin:0;padding:16px 14px 40px;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.65;-webkit-text-size-adjust:100%}}
.wrap{{max-width:680px;margin:0 auto}}
header{{margin-bottom:18px}}
h1{{font-size:19px;font-weight:600;margin:0 0 6px}}
.sub{{font-size:13px;color:var(--ink2)}}
.tip{{margin-top:12px;padding:10px 12px;background:#fff8e6;border:1px solid #f0dfb8;border-radius:10px;font-size:13px;color:#7a5b0b}}
.bar{{display:flex;gap:8px;margin:16px 0 4px}}
.bar button{{flex:1;padding:9px 0;font-size:13px;border:1px solid var(--line);background:var(--card);color:var(--ink2);border-radius:9px;cursor:pointer}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:12px 0;overflow:hidden}}
.q{{padding:14px 15px;display:flex;gap:11px;align-items:flex-start;cursor:pointer;list-style:none}}
.q::-webkit-details-marker{{display:none}}
.q:hover{{background:#faf9f6}}
.no{{flex:0 0 26px;height:26px;border-radius:8px;background:var(--ink);color:#fff;font-size:13px;display:flex;align-items:center;justify-content:center;margin-top:1px}}
.qmain{{flex:1;min-width:0}}
.term{{font-size:16px;font-weight:600;line-height:1.4}}
.meta{{margin-top:5px;display:flex;flex-wrap:wrap;gap:6px}}
.tag{{font-size:11px;padding:2px 7px;border-radius:5px;background:#f1efe8;color:var(--ink2)}}
.tag.hot{{background:var(--accent-bg);color:var(--accent);font-weight:500}}
.hint{{font-size:12px;color:var(--ink3);margin-top:6px}}
.a{{padding:0 15px 15px 52px;border-top:1px dashed var(--line)}}
.a h4{{margin:14px 0 6px;font-size:13px;color:var(--ink2);font-weight:600}}
.def{{font-size:14.5px;margin:0}}
ol{{margin:0;padding-left:20px}}
ol li{{font-size:14px;margin:5px 0}}
.mn{{background:var(--ok-bg);border-radius:8px;padding:9px 11px;font-size:13.5px;color:#27500a}}
.src{{font-size:11.5px;color:var(--ink3);margin-top:10px;line-height:1.6}}
footer{{margin-top:26px;font-size:11.5px;color:var(--ink3);text-align:center;line-height:1.7}}
</style>
</head>
<body>
<div class="wrap">
<header>
<h1>{title}</h1>
<div class="sub">{sub}</div>
<div class="tip">先自己在心里答一遍，再点题目展开答案。答不出的，标记下来当天背熟。</div>
</header>
<div class="bar">
<button onclick="allOpen(true)">全部展开</button>
<button onclick="allOpen(false)">全部收起</button>
</div>
{cards}
<footer>{footer}</footer>
</div>
<script>
function allOpen(v){{document.querySelectorAll('details').forEach(function(d){{d.open=v}})}}
</script>
</body>
</html>"""

CARD = """<details class="card">
<summary class="q">
<span class="no">{no}</span>
<span class="qmain">
<span class="term">{term}</span>
<span class="meta">{tags}</span>
<span class="hint">点一下展开答案</span>
</span>
</summary>
<div class="a">
<h4>定义</h4>
<p class="def">{definition}</p>
<h4>答题要点</h4>
<ol>{points}</ol>
<h4>记忆锚点</h4>
<div class="mn">{mnemonic}</div>
<div class="src">{source_note}</div>
</div>
</details>"""


def pick(bank, n):
    fresh = [it for it in bank["items"] if not it.get("used_on")]
    return fresh[:n]


def build_card(no, item):
    tags = []
    for y in item.get("years", []):
        tags.append('<span class="tag hot">真题 %s</span>' % y)
    for t in item.get("tags", []):
        tags.append('<span class="tag">%s</span>' % t)
    if len(item.get("years", [])) > 1:
        tags.append('<span class="tag hot">高频 · 考过 %d 次</span>' % len(item["years"]))
    points = "".join("<li>%s</li>" % p for p in item["points"])
    return CARD.format(
        no=no,
        term=item["term"],
        tags="".join(tags),
        definition=item["definition"],
        points=points,
        mnemonic=item["mnemonic"],
        source_note=item["source_note"],
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--count", type=int, default=PER_DAY)
    args = ap.parse_args()

    today = args.date or datetime.date.today().isoformat()
    bank = json.load(open(BANK, encoding="utf-8"))
    picked = pick(bank, args.count)
    if not picked:
        print(json.dumps({"error": "题库已出尽，需要补充新词条"}, ensure_ascii=False))
        return 1

    cards = "".join(build_card(i + 1, it) for i, it in enumerate(picked))
    total = len(bank["items"])
    done = sum(1 for it in bank["items"] if it.get("used_on"))
    html = TPL.format(
        title="%s · 专业一名词解释 %d 题" % (today, len(picked)),
        sub="北京电影学院 艺术基础理论 · 真题优先 · 第 %d 期" % (done // args.count + 1),
        cards=cards,
        footer="题库进度 %d/%d · 真题优先批次<br>答案来源：zhenti.md 可溯源真题 + 通识补充 [补]，教材未覆盖处已标注，遇到存疑条目请回教材核实",
    )

    if args.dry_run:
        print(json.dumps({"date": today, "picked": [it["term"] for it in picked]},
                         ensure_ascii=False, indent=2))
        return 0

    os.makedirs(PAGES, exist_ok=True)
    path = os.path.join(PAGES, "%s.html" % today)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join(PAGES, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    for it in picked:
        it["used_on"] = today
    bank["meta"]["updated"] = today
    with open(BANK, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "date": today,
        "path": path,
        "terms": [it["term"] for it in picked],
        "years": [it.get("years", []) for it in picked],
        "remaining": len([it for it in bank["items"] if not it.get("used_on")]),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
