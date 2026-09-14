#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给题库里的词条分配固定顺序 seq，实现真题与补充概念混合。

规则：
- 已推送过的题目（used_on 非空）优先排在最前，保留历史。
- 其余题目按固定种子随机打乱，避免一天全是真题或全是补充。
- 已有 seq 的条目会被重新分配（仅在新增条目时运行）。
"""
import json
import os
import random

BASE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(BASE, "题库.json")
SEED = 20260914


def seeded_shuffle(seq, seed):
    r = random.Random(seed)
    out = list(seq)
    r.shuffle(out)
    return out


def main():
    bank = json.load(open(BANK, encoding="utf-8"))
    items = bank["items"]
    for it in items:
        it.pop("seq", None)  # 先全部清空，确保重新分配

    used = [it for it in items if it.get("used_on")]
    fresh = [it for it in items if not it.get("used_on")]

    # 已推送按 used_on 日期 + 原顺序稳定排在前头
    used.sort(key=lambda x: x.get("used_on", ""))

    # 其余按固定种子打乱
    fresh = seeded_shuffle(fresh, SEED)

    for i, it in enumerate(used):
        it["seq"] = i + 1
    for i, it in enumerate(fresh):
        it["seq"] = len(used) + i + 1

    json.dump(bank, open(BANK, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("已分配 %d 条 seq；已推送 %d 条在前，未推送 %d 条打乱在后" % (
        len(items), len(used), len(fresh)))


if __name__ == "__main__":
    main()
