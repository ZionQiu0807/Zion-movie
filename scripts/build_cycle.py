#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给题库打上「轮次轨道」：真题 29 条 / 补充 116 条，并写入固定顺序位。

每天推送 = 1 道真题 + 4 道补充（真题夹在中间），两池各自按顺序循环：
  真题 29 条 → 29 天一轮
  补充 116 条 → 4×29 = 116，同为 29 天一轮
两池同步换轮，一轮之内不出现重复题目。

顺序位字段：
  track        : "真题" | "补充"
  zhenti_pos   : 真题池内的固定序号（0..28）
  buchong_pos  : 补充池内的固定序号（0..115）

真题池排序规则：
  第 0 位固定为 2026-09-14 当天已推过的「汉画像石」；其余真题按 seq；
  同一批在 9/14 已经露过面的另外 4 条（宝莱坞/史东山/孤岛电影/《闲情偶寄》）
  挪到本轮最后，避免刚看过又重复。
补充池用固定随机种子打乱，让教材概念、真题衍生概念与新补充条目均匀分散。
"""
import json
import os
import random

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(BASE, "题库.json")
SEED = 20260914
FIRST_TERM = "汉画像石"
SEEN_ON = "2026-09-14"


def main():
    bank = json.load(open(BANK, encoding="utf-8"))
    items = bank["items"]

    zhenti, buchong = [], []
    for it in items:
        it["track"] = "真题" if it.get("origin") == "真题" else "补充"
        (zhenti if it["track"] == "真题" else buchong).append(it)

    # 真题池顺序
    def zkey(it):
        if it["term"] == FIRST_TERM:
            return (0, -1)
        if it.get("used_on") == SEEN_ON:
            return (2, it.get("seq", 0))
        return (1, it.get("seq", 0))

    zhenti.sort(key=zkey)
    for i, it in enumerate(zhenti):
        it["zhenti_pos"] = i
        it.pop("buchong_pos", None)

    # 补充池顺序：固定种子打乱
    order = list(range(len(buchong)))
    random.Random(SEED).shuffle(order)
    buchong_pos_of = {}
    for pos, idx in enumerate(order):
        buchong_pos_of[id(buchong[idx])] = pos
    for it in buchong:
        it["buchong_pos"] = buchong_pos_of[id(it)]
        it.pop("zhenti_pos", None)

    bank["meta"]["order_rule"] = ("每天 1 道真题（29 条一轮）+ 4 道补充（116 条一轮），"
                                 "两池同步 29 天一轮；补充池以固定种子 %d 打乱" % SEED)
    bank["meta"]["composition"] = {"真题": len(zhenti), "补充": len(buchong),
                                   "daily": "1 真题 + 4 补充", "round_days": len(zhenti)}
    with open(BANK, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=1)

    print("真题池 %d 条 → %d 天一轮" % (len(zhenti), len(zhenti)))
    print("补充池 %d 条 → 每天 4 道 = %.2f 天一轮" % (len(buchong), len(buchong) / 4))
    if len(buchong) % 4 == 0:
        print("两池轮长%s" % ("一致 ✅" if len(buchong) // 4 == len(zhenti)
                            else "不一致（补充 %d 天 / 真题 %d 天）" % (len(buchong) // 4, len(zhenti))))
    else:
        print("注意：补充池不是 4 的整数倍，轮末会有轻微错位")
    print()
    print("真题前 6 位：", " / ".join(it["term"] for it in zhenti[:6]))
    print("真题后 5 位：", " / ".join(it["term"] for it in zhenti[-5:]))
    b_sorted = sorted(buchong, key=lambda x: x["buchong_pos"])
    print("补充前 8 位：", " / ".join(it["term"] for it in b_sorted[:8]))


if __name__ == "__main__":
    main()
