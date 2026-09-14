#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 4 份扩充结果合并进题库，并校验页码出处真实性。"""
import glob
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(BASE, "题库.json")
VERIFY = os.path.join(BASE, "verify")


def main():
    bank = json.load(open(BANK, encoding="utf-8"))
    have_seq = {i.get("seq") for i in bank["items"]}
    plan = json.load(open(os.path.join(VERIFY, "扩充选中.json"), encoding="utf-8"))
    plan_by_seq = {f["seq"]: f for f in plan["items"]}

    new_items = {}
    for f in sorted(glob.glob(os.path.join(VERIFY, "扩充结果_批次*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        for it in d["items"]:
            if it["seq"] in new_items:
                print("警告：seq %s 重复" % it["seq"])
            new_items[it["seq"]] = it

    problems = []
    if len(new_items) != len(plan_by_seq):
        problems.append("条目数不符：结果 %d vs 计划 %d" % (len(new_items), len(plan_by_seq)))

    out = []
    for seq in sorted(plan_by_seq):
        f = plan_by_seq[seq]
        it = new_items.get(seq)
        if not it:
            problems.append("seq %s（%s）缺结果" % (seq, f["target"]))
            continue
        if it["term"] != f["target"]:
            problems.append("seq %s 名词不一致：计划=%s 结果=%s" % (seq, f["target"], it["term"]))
        if seq in have_seq:
            problems.append("seq %s 与题库既有条目冲突" % seq)

        dfn = it.get("definition", "")
        if not (40 <= len(dfn) <= 260):
            problems.append("seq %s（%s）定义长度异常 %d" % (seq, it["term"], len(dfn)))
        pts = it.get("points") or []
        if not (3 <= len(pts) <= 6):
            problems.append("seq %s（%s）要点数 %d（应为 3-6）" % (seq, it["term"], len(pts)))
        if not it.get("mnemonic"):
            problems.append("seq %s（%s）缺记忆锚点" % (seq, it["term"]))

        sn = it.get("source_note", "")
        if "核对通过" not in sn:
            problems.append("seq %s（%s）出处未注明核对通过" % (seq, it["term"]))
        pages = {str(h["page"]) for h in f["hits"]}
        books = {h["book"] for h in f["hits"]}
        for m in re.finditer(r"P\s*(\d+)", sn):
            if m.group(1) not in pages:
                problems.append("seq %s（%s）引用 P%s 不在候选页码 %s 中" % (seq, it["term"], m.group(1), ",".join(sorted(pages))))
        for b in books:
            if b in sn:
                break
        else:
            problems.append("seq %s（%s）出处未见任何候选书名" % (seq, it["term"]))

        out.append({
            "id": "b%03d" % seq,
            "term": it["term"],
            "subject": "专业一",
            "origin": "教材",
            "src_book": it.get("src_book", ""),
            "years": [],
            "tags": it.get("tags", []),
            "definition": dfn,
            "points": pts,
            "mnemonic": it["mnemonic"],
            "source_note": sn,
            "verified": "matched",
            "verify_change": "新补充条目，依据教材原文写入",
            "used_on": None,
            "seq": seq,
        })

    print("新增条目：%d 条" % len(out))
    print("问题：%d" % len(problems))
    for p in problems:
        print("  -", p)

    bank["items"].extend(out)
    bankset = json.load(open(os.path.join(BASE, "题库.json.bak"), encoding="utf-8")) if os.path.exists(os.path.join(BASE, "题库.json.bak")) else None
    with open(os.path.join(BASE, "题库.json"), "w", encoding="utf-8") as fh:
        json.dump(bank, fh, ensure_ascii=False, indent=1)
    print("题库现在共 %d 条" % len(bank["items"]))


if __name__ == "__main__":
    main()
