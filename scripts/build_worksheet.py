#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核对工作单生成器。

把题库每条名词与三本教材的全量读书笔记（notes/全书笔记.json）做匹配，
为每条抽出「书中原文候选段落」（含书/页/章节），供后续逐条核对。

输出：
  verify/核对工作单.json   —— 结构化，含每条题目 + 匹配到的原文段落
  verify/工作单_批次NN.md  —— 人/子agent 可读版，每批 15 条
"""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES = os.path.join(BASE, "notes", "全书笔记.json")
BANK = os.path.join(BASE, "题库.json")
OUTDIR = os.path.join(BASE, "verify")
BATCH = 15
MAX_PASSAGES = 4

STRIP = "《》「」“”\"'（）()·，,。.：:；;、—－-　 "


def norm(s):
    if not s:
        return ""
    for ch in STRIP:
        s = s.replace(ch, "")
    return s.strip().lower()


def load_concepts():
    """展平全书笔记为概念列表。"""
    d = json.load(open(NOTES, encoding="utf-8"))
    out = []
    for book, pages in d["books"].items():
        for p in pages:
            for c in p.get("concepts", []):
                out.append({
                    "book": book,
                    "page": p.get("page"),
                    "printed_page": p.get("printed_page", ""),
                    "chapter": p.get("chapter_title", ""),
                    "section": p.get("section_title", ""),
                    "term": c.get("term", ""),
                    "definition": c.get("definition", ""),
                    "keywords": c.get("keywords") or [],
                    "examples": c.get("examples") or [],
                })
    return out


def score(query, nq, c):
    """给候选概念打分，越高越相关。"""
    nt = norm(c["term"])
    if not nt:
        return 0
    if nt == nq:
        return 100
    if nq and nq in nt:
        return 85 - min(len(nt) - len(nq), 20)
    if nt and nt in nq:
        return 78 - min(len(nq) - len(nt), 20)
    body = norm(c["definition"]) + norm("".join(c["keywords"])) + norm("".join(c["examples"]))
    if nq and len(nq) >= 2 and nq in body:
        return 55
    # 关键词交叉：query 被拆成 2 字以上片段命中
    if len(nq) >= 4:
        for i in range(0, len(nq) - 3):
            frag = nq[i:i + 4]
            if frag in nt:
                return 45
    return 0


def main():
    bank = json.load(open(BANK, encoding="utf-8"))
    concepts = load_concepts()
    os.makedirs(OUTDIR, exist_ok=True)

    items = sorted(bank["items"], key=lambda x: x.get("seq", 10 ** 9))
    results = []
    for it in items:
        raw = it["term"]
        # 主要查询串：去掉书名号等包裹
        nq = norm(raw)
        scored = []
        for c in concepts:
            s = score(raw, nq, c)
            if s > 0:
                scored.append((s, c))
        scored.sort(key=lambda x: -x[0])
        picked = []
        seen = set()
        for s, c in scored:
            key = (c["book"], c["page"], c["term"])
            if key in seen:
                continue
            seen.add(key)
            picked.append({
                "score": s, "book": c["book"], "page": c["page"],
                "chapter": c["chapter"], "section": c["section"],
                "term": c["term"], "definition": c["definition"],
                "keywords": c["keywords"], "examples": c["examples"],
            })
            if len(picked) >= MAX_PASSAGES:
                break
        results.append({
            "seq": it.get("seq"),
            "term": raw,
            "origin": it.get("origin"),
            "years": it.get("years", []),
            "subject": it.get("subject"),
            "tags": it.get("tags", []),
            "definition": it.get("definition", ""),
            "points": it.get("points", []),
            "mnemonic": it.get("mnemonic", ""),
            "source_note": it.get("source_note", ""),
            "passages": picked,
        })

    with open(os.path.join(OUTDIR, "核对工作单.json"), "w", encoding="utf-8") as f:
        json.dump({"items": results}, f, ensure_ascii=False, indent=1)

    # 人/子agent 可读版，分批
    nbatch = (len(results) + BATCH - 1) // BATCH
    files = []
    for bi in range(nbatch):
        chunk = results[bi * BATCH:(bi + 1) * BATCH]
        lines = ["# 核对工作单 批次 %02d（共 %d 批）" % (bi + 1, nbatch), ""]
        for r in chunk:
            lines.append("## 第 %s 条 · %s" % (r["seq"], r["term"]))
            lines.append("- 标注：origin=%s | years=%s | tags=%s" % (r["origin"], "/".join(r["years"]) or "无", "/".join(r["tags"])))
            lines.append("- **当前定义**：%s" % r["definition"])
            for i, p in enumerate(r["points"], 1):
                lines.append("  - 要点%d：%s" % (i, p))
            lines.append("- 记忆锚点：%s" % r["mnemonic"])
            lines.append("- 当前出处标注：%s" % r["source_note"])
            if r["passages"]:
                lines.append("- **书中原文候选**：")
                for p in r["passages"]:
                    lines.append("  - [%s P%s | %s | %s] **%s**：%s" % (
                        p["book"], p["page"], p["chapter"], p["section"][:40], p["term"], p["definition"]))
            else:
                lines.append("- **书中原文候选**：（三本书中未匹配到）")
            lines.append("")
        name = "工作单_批次%02d.md" % (bi + 1)
        with open(os.path.join(OUTDIR, name), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        files.append(name)

    matched = sum(1 for r in results if r["passages"])
    high = sum(1 for r in results if r["passages"] and r["passages"][0]["score"] >= 78)
    print("条目 %d 条 | 匹配到原文 %d 条 | 高分匹配(>=78) %d 条 | 未匹配 %d 条" % (
        len(results), matched, high, len(results) - matched))
    print("批次文件：%d 个，位于 verify/" % len(files))
    print()
    print("未匹配到原文的条目：")
    for r in results:
        if not r["passages"]:
            print("  %2s %s（%s）" % (r["seq"], r["term"], r["origin"]))
    print()
    print("低分匹配（可能有误，需重点看）：")
    for r in results:
        if r["passages"] and r["passages"][0]["score"] < 78:
            p = r["passages"][0]
            print("  %2s %s -> [%s P%s] %s (score=%s)" % (r["seq"], r["term"], p["book"], p["page"], p["term"], p["score"]))


if __name__ == "__main__":
    main()
