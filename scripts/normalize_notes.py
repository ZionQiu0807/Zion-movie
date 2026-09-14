# -*- coding: utf-8 -*-
"""整理三本书的阅读笔记：
1. 补齐缺失的 page 字段
2. 合并为一份可检索总笔记 notes/全书笔记.json
3. 生成概念索引 notes/概念索引.md（便于人工查阅）
"""
import json, os, re, glob
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES = os.path.join(BASE, "notes")

BOOK_ORDER = ["艺术学概论", "中国电影史", "外国电影史"]

merged = {b: [] for b in BOOK_ORDER}
stats = {}

for f in sorted(glob.glob(os.path.join(NOTES, "*.json"))):
    name = os.path.basename(f)
    if name in ("全书笔记.json",):
        continue
    m = re.match(r"(.+?)_(\d+)_(\d+)\.json", name)
    if not m:
        continue
    book, s, e = m.group(1), int(m.group(2)), int(m.group(3))
    d = json.load(open(f, encoding="utf-8"))
    fixed = 0
    for i, p in enumerate(d.get("pages", [])):
        if not p.get("page"):
            p["page"] = s + i
            fixed += 1
    if fixed:
        json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    for p in d.get("pages", []):
        merged.setdefault(book, []).append(p)
    stats[name] = {"fixed": fixed, "pages": len(d.get("pages", []))}

out = {"books": {}, "total_pages": 0, "total_concepts": 0}
for b in BOOK_ORDER:
    pages = sorted(merged.get(b, []), key=lambda x: x.get("page") or 0)
    tc = sum(len(p.get("concepts", [])) for p in pages)
    out["books"][b] = pages
    out["total_pages"] += len(pages)
    out["total_concepts"] += tc
    print("%-8s %3d 页  %4d 概念" % (b, len(pages), tc))

json.dump(out, open(os.path.join(NOTES, "全书笔记.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\n合计 %d 页 / %d 概念" % (out["total_pages"], out["total_concepts"]))
print("已写 notes/全书笔记.json")

# 概念索引
lines = ["# 三本书概念索引", "",
         "共 %d 页 / %d 个概念。" % (out["total_pages"], out["total_concepts"]), ""]
for b in BOOK_ORDER:
    lines.append("## %s" % b)
    lines.append("")
    for p in out["books"][b]:
        cs = p.get("concepts", [])
        if not cs:
            continue
        head = "### p%s %s" % (p.get("page"), p.get("section_title") or p.get("chapter_title") or "")
        lines.append(head)
        for c in cs:
            term = c.get("term", "").strip()
            dfn = (c.get("definition") or "").strip().replace("\n", " ")
            if len(dfn) > 200:
                dfn = dfn[:200] + "…"
            lines.append("- **%s**：%s" % (term, dfn))
        lines.append("")
open(os.path.join(NOTES, "概念索引.md"), "w", encoding="utf-8").write("\n".join(lines))
print("已写 notes/概念索引.md")

# 概念名 -> 位置索引
idx = defaultdict(list)
for b in BOOK_ORDER:
    for p in out["books"][b]:
        for c in p.get("concepts", []):
            t = (c.get("term") or "").strip()
            if t:
                idx[t].append({"book": b, "page": p.get("page"),
                               "section": p.get("section_title") or p.get("chapter_title")})
json.dump(idx, open(os.path.join(NOTES, "概念位置索引.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("已写 notes/概念位置索引.json（%d 个不同概念名）" % len(idx))
