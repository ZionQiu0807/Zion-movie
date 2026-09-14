#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扩充题库：从三本书笔记中新增 55 条「补充」题目，并生成给写手的任务单。

选中的 55 个名词按考点分布配比：
  艺术概论与各艺术门类 25 / 中国电影史 15 / 外国电影史 15
正好让「每天 1 道真题 + 4 道补充」的配比凑成完整一轮：
  真题 29 条 → 29 天；补充 116 条 → 4×29 = 116。两池同步换轮，无重复。
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIFY = os.path.join(BASE, "verify")

CHOSEN = {
    "艺术概论与艺术门类": [
        "客观精神说", "主观精神说", "艺术典型", "典型环境", "审美直觉", "通感", "共鸣",
        "召唤结构", "艺术意蕴", "意象", "风格即人", "绘画六法", "气韵生动", "以形写神",
        "工笔画", "写意画", "书法艺术", "园林艺术", "借景", "表情艺术", "旋律",
        "舞蹈艺术", "芭蕾舞", "电影艺术", "正剧",
    ],
    "中国电影史": [
        "《定军山》", "《难夫难妻》", "《孤儿救祖记》", "明星影片公司", "左翼电影",
        "国防电影", "蔡楚生", "《渔光曲》", "费穆", "《小城之春》", "延安电影团",
        "十七年电影", "样板戏电影", "谢晋", "第五代导演",
    ],
    "外国电影史": [
        "梅里爱", "《月球旅行记》", "格里菲斯", "《一个国家的诞生》", "库里肖夫效应",
        "《战舰波将金号》", "蒙太奇学派", "德国表现主义", "《卡里加里博士》", "海斯法典",
        "西部片", "《公民凯恩》", "法国诗意现实主义", "法国新浪潮", "左岸派",
    ],
}
BATCH = 14


def main():
    cand = json.load(open(os.path.join(VERIFY, "扩充候选.json"), encoding="utf-8"))
    by_target = {r["target"]: r["hits"] for r in cand["targets"]}

    flat = []
    for group, targets in CHOSEN.items():
        for t in targets:
            hits = by_target.get(t, [])
            flat.append({"group": group, "target": t, "hits": hits})
    print("选中 %d 个名词" % len(flat))
    missing = [f["target"] for f in flat if not f["hits"]]
    if missing:
        print("警告：以下无原文候选", missing)

    # 分配 seq：91 起
    for i, f in enumerate(flat):
        f["seq"] = 91 + i

    nbatch = (len(flat) + BATCH - 1) // BATCH
    for bi in range(nbatch):
        chunk = flat[bi * BATCH:(bi + 1) * BATCH]
        lines = ["# 扩充题目写作任务单 批次 %02d（共 %d 批）" % (bi + 1, nbatch), "",
                 "以下每条都给出了**三本教材的原书段落**（含书名、页码、章节）。请据此写成可直接推送的名词解释条目。", ""]
        for f in chunk:
            lines.append("## seq %d · %s  （分类：%s）" % (f["seq"], f["target"], f["group"]))
            lines.append("")
            for h in f["hits"][:3]:
                lines.append("- 原文 **[%s P%s | %s | %s]** **%s**" % (
                    h["book"], h["page"], h["chapter"][:18], h["section"][:40], h["term"]))
                lines.append("  - 定义：%s" % h["definition"])
                if h.get("keywords"):
                    lines.append("  - 关键词：%s" % "、".join(h["keywords"][:8]))
                if h.get("examples"):
                    lines.append("  - 例子：%s" % "、".join(h["examples"][:5]))
            lines.append("")
        with open(os.path.join(VERIFY, "扩充工作单_批次%02d.md" % (bi + 1)), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
    print("已写出 %d 个任务单到 verify/" % nbatch)
    with open(os.path.join(VERIFY, "扩充选中.json"), "w", encoding="utf-8") as fh:
        json.dump({"items": flat}, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
