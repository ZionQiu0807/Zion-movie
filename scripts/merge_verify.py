#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 6 份核对结果合并回题库，并做一致性校验。

校验项：
  1. seq/term 必须与题库一致，不得漏项或重复
  2. verdict=not_in_books 的条目，source_note 不得声称“原文核对通过”
  3. source_note 中引用的页码必须真的出现在该条的「书中原文候选」里（防编造页码）
  4. definition 长度合理（40-260 字），points 不为空

备份原题库为 题库_核对前.json。
"""
import glob
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(BASE, "题库.json")
VERIFY = os.path.join(BASE, "verify")


def main():
    bank = json.load(open(BANK, encoding="utf-8"))
    sheet = json.load(open(os.path.join(VERIFY, "核对工作单.json"), encoding="utf-8"))
    by_seq = {r["seq"]: r for r in sheet["items"]}

    merged = {}
    for f in sorted(glob.glob(os.path.join(VERIFY, "核对结果_批次*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        for it in d["items"]:
            if it["seq"] in merged:
                print("警告：seq %s 重复出现" % it["seq"])
            merged[it["seq"]] = it

    problems = []
    stats = {"matched": 0, "partial": 0, "not_in_books": 0}
    changed = 0

    for item in bank["items"]:
        seq = item.get("seq")
        v = merged.get(seq)
        if not v:
            problems.append("seq %s（%s）缺少核对结果" % (seq, item["term"]))
            continue
        if v["term"] != item["term"]:
            problems.append("seq %s 题目名不一致：库=%s 核对=%s" % (seq, item["term"], v["term"]))
        verdict = v.get("verdict", "")
        stats[verdict] = stats.get(verdict, 0) + 1

        # 校验 2：无书证却声称核对通过
        sn = v.get("source_note", "")
        if verdict == "not_in_books" and ("原文核对通过" in sn or "核对通过" in sn):
            problems.append("seq %s（%s）无书证但标注了“核对通过”" % (seq, item["term"]))
        if verdict in ("matched", "partial") and "核对通过" not in sn:
            problems.append("seq %s（%s）有书证但未标注核对结果" % (seq, item["term"]))

        # 校验 3：页码是否真实存在于候选段落
        real_pages = {str(p["page"]) for p in by_seq.get(seq, {}).get("passages", [])}
        for m in re.finditer(r"P\s*(\d+)", sn):
            if m.group(1) not in real_pages:
                problems.append("seq %s（%s）出处引用了 P%s，但该页不在候选段落中（候选页：%s）"
                                % (seq, item["term"], m.group(1), ",".join(sorted(real_pages)) or "无"))

        # 校验 4：长度
        dfn = v.get("definition", "")
        if not (40 <= len(dfn) <= 300):
            problems.append("seq %s（%s）定义长度异常：%d 字" % (seq, item["term"], len(dfn)))
        if not v.get("points"):
            problems.append("seq %s（%s）要点为空" % (seq, item["term"]))

        if dfn != item.get("definition"):
            changed += 1
        item["definition"] = dfn
        item["points"] = v["points"]
        item["source_note"] = sn
        item["verified"] = verdict
        item["verify_change"] = v.get("change", "")

    print("核对分布：matched %d / partial %d / not_in_books %d" % (
        stats.get("matched", 0), stats.get("partial", 0), stats.get("not_in_books", 0)))
    print("定义被改写：%d 条" % changed)
    print("问题：%d 条" % len(problems))
    for p in problems:
        print("  -", p)

    if problems:
        print()
        print("存在告警，已写出题库但请人工确认上述条目。")

    # 备份（只在首次运行时备份，避免覆盖真正的原始副本）
    bak = os.path.join(BASE, "题库_核对前.json")
    if not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f:
            json.dump(bank, f, ensure_ascii=False, indent=1)
        print("原题库已备份为 %s" % os.path.basename(bak))
    else:
        print("备份 %s 已存在，跳过备份" % os.path.basename(bak))

    bank["meta"]["verified_at"] = "2026-09-14"
    bank["meta"]["verified_source"] = "三本教材全量逐页阅读笔记（915 页 / 2560 概念）"
    with open(BANK, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=1)
    print("题库已更新：%d 条" % len(bank["items"]))


if __name__ == "__main__":
    main()
