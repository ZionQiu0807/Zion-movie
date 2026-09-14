#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量更新 source_note，把教材概念的 [补] 替换为更具体的章节来源。
真题名词不在彭吉象教材中的，明确标注需其他参考书核对。"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(BASE, "题库.json")

BOOK = "彭吉象《艺术学概论》（第6版）"

CHAPTER_MAP = [
    (("艺术起源",), f"{BOOK} 第2章 艺术的起源"),
    (("艺术作品", "内容与形式"), f"{BOOK} 第11章 艺术作品"),
    (("艺术创作", "创作方法", "创作论"), f"{BOOK} 第10章 艺术创作"),
    (("艺术鉴赏",), f"{BOOK} 第12章 艺术鉴赏"),
    (("艺术功能", "美育"), f"{BOOK} 第3章 艺术的功能与艺术教育"),
    (("实用艺术",), f"{BOOK} 第5章 实用艺术"),
    (("造型艺术",), f"{BOOK} 第6章 造型艺术"),
    (("表情艺术",), f"{BOOK} 第7章 表情艺术"),
    (("综合艺术", "戏剧", "戏曲", "电影语言"), f"{BOOK} 第8章 综合艺术"),
    (("语言艺术",), f"{BOOK} 第9章 语言艺术"),
    (("中国美学", "画论", "传神论", "中国传统艺术精神"), f"{BOOK} 第11章 中国传统艺术精神 / 第6章 造型艺术"),
    (("当代艺术", "当代理论", "数字艺术", "文化工业", "商品化"), f"{BOOK} 第4章 文化系统中的艺术"),
    (("电影理论", "类型电影", "作者论"), f"{BOOK} 第4章 文化系统中的艺术 / 第8章 综合艺术"),
    (("马克思主义", "艺术生产", "艺术本质"), f"{BOOK} 第1章 艺术的本质与特征"),
    (("美学范畴", "悲剧", "崇高", "优美"), f"{BOOK} 第1章 / 第5章 / 第11章（美学范畴相关章节）"),
]

OUTSIDE_NOTE = "该概念超出彭吉象《艺术学概论》范围；来源：zhenti.md 可溯源真题；答案依据通识/艺术史/电影史 [补] 待教材或专著核实"


def match_chapter(tags):
    for keys, chapter in CHAPTER_MAP:
        for k in keys:
            if any(k in t for t in tags):
                return chapter
    return BOOK


def update_item(it):
    origin = it.get("origin", "")
    tags = it.get("tags", [])
    if origin == "教材":
        chapter = match_chapter(tags)
        it["source_note"] = "来源：%s；答案依据教材梳理" % chapter
        return True
    elif origin == "真题隐含":
        # 电影史/美术史/文学/外国艺术史实等 明确标为教材外
        if any(t in tags for t in ("中国电影史", "外国电影史", "美术史", "古典文学", "影片", "导演")):
            it["source_note"] = OUTSIDE_NOTE
            return True
        # 戏曲理论 / 戏剧 可在第8章
        if any(t in tags for t in ("戏曲理论", "戏剧")):
            it["source_note"] = "来源：%s 第8章 综合艺术；答案依据教材梳理" % BOOK
            return True
        # 其余真题隐含概念按 tags 匹配章节
        chapter = match_chapter(tags)
        it["source_note"] = "来源：%s；答案依据教材梳理（原在 zhenti.md 简答/论述中出现）" % chapter
        return True
    elif origin == "真题":
        # 真题原词绝大多数是美术史/电影史/文学史，不在彭吉象书里
        it["source_note"] = OUTSIDE_NOTE
        return True
    return False


def main():
    bank = json.load(open(BANK, encoding="utf-8"))
    n = 0
    for it in bank["items"]:
        if update_item(it):
            n += 1
    json.dump(bank, open(BANK, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("已更新 %d 条 source_note" % n)


if __name__ == "__main__":
    main()
