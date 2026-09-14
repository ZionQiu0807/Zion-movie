#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扩充候选检索：给一批目标名词，从三本书笔记里找出对应的原书段落。

输出 verify/扩充候选.md（人/子agent 可读）与 verify/扩充候选.json。
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES = os.path.join(BASE, "notes", "全书笔记.json")
OUT = os.path.join(BASE, "verify")

TARGETS = [
    # —— 艺术理论 / 艺术概论体系 ——
    "客观精神说", "主观精神说", "艺术生产论", "艺术意蕴", "艺术典型", "典型环境",
    "审美直觉", "通感", "联觉", "共鸣", "召唤结构", "艺术修养", "艺术鉴赏力",
    "艺术体验", "艺术传达", "艺术构思", "形象思维", "抽象思维", "灵感思维",
    "风格即人", "艺术思潮", "艺术流派", "艺术语言", "艺术形象", "艺术真实",
    "审美教育", "艺术教育的任务", "寓教于乐", "审美娱乐功能", "艺术的认识功能",
    "绘画六法", "气韵生动", "以形写神", "文人画", "工笔画", "写意画", "题画诗",
    "书法艺术", "篆刻", "园林艺术", "借景", "分景", "隔景", "工艺美术",
    "表情艺术", "音乐艺术", "舞蹈艺术", "节奏", "韵律", "旋律", "交响乐", "芭蕾舞",
    "实用艺术", "建筑艺术", "设计艺术", "戏曲艺术", "虚拟性", "程式化", "脸谱",
    "戏剧艺术", "悲剧", "喜剧", "正剧", "话剧", "电影艺术", "电视剧艺术",
    "语言艺术", "诗歌", "散文", "小说", "典型人物", "意境", "意象",
    "艺术与科学", "艺术与宗教", "艺术与哲学", "艺术与道德", "艺术生产",
    "蒙太奇", "长镜头", "景深", "画外音", "声画同步", "声画对位", "电影符号学",
    "艺术接受", "审美再创造", "艺术批评的标准",
    # —— 中国电影史 ——
    "《定军山》", "《难夫难妻》", "《孤儿救祖记》", "明星影片公司", "《火烧红莲寺》",
    "《神女》", "《马路天使》", "《十字街头》", "《渔光曲》", "蔡楚生", "费穆",
    "《小城之春》", "《一江春水向东流》", "《八千里路云和月》", "《万家灯火》",
    "《乌鸦与麻雀》", "郑君里", "石挥", "《我这一辈子》", "《林家铺子》",
    "《早春二月》", "谢晋", "《红色娘子军》", "《五朵金花》", "样板戏电影",
    "《黄土地》", "《红高粱》", "第五代导演", "第四代导演", "《一个和八个》",
    "《芙蓉镇》", "战争片", "反特片", "十七年电影", "《桥》", "《武训传》",
    "昆仑影业公司", "文华影业公司", "延安电影团", "《延安与八路军》", "左翼电影",
    "国防电影", "软性电影", "《渔光曲》",
    # —— 外国电影史 ——
    "梅里爱", "《月球旅行记》", "格里菲斯", "《一个国家的诞生》", "《党同伐异》",
    "库里肖夫效应", "爱森斯坦", "《战舰波将金号》", "普多夫金", "蒙太奇学派",
    "德国表现主义", "《卡里加里博士》", "法国印象派电影", "超现实主义电影",
    "《一条安达鲁狗》", "《爵士歌王》", "好莱坞制片厂制度", "海斯法典",
    "西部片", "奥逊·威尔斯", "《公民 Kane》", "《公民凯恩》", "法国诗意现实主义",
    "让·雷诺阿", "《游戏规则》", "法国新浪潮", "《四百击》", "特吕弗", "戈达尔",
    "《精疲力尽》", "左岸派", "《广岛之恋》", "阿伦·雷乃", "《电影手册》",
    "德国新电影", "法斯宾德", "新好莱坞", "《邦妮与克莱德》", "黑泽明", "《罗生门》",
    "小津安二郎", "沟口健二", "瑞典电影", "伯格曼", "苏联电影", "《母亲》",
]


def norm(s):
    for ch in "《》「」“”\"'（）()·，,。.：:；;、—－-　 ":
        s = s.replace(ch, "")
    return s.strip().lower()


def main():
    d = json.load(open(NOTES, encoding="utf-8"))
    concepts = []
    for bk, pages in d["books"].items():
        for p in pages:
            for c in p.get("concepts", []):
                concepts.append({
                    "book": bk, "page": p["page"],
                    "chapter": p.get("chapter_title", ""),
                    "section": p.get("section_title", ""),
                    "term": c.get("term", ""), "definition": c.get("definition", ""),
                    "keywords": c.get("keywords") or [], "examples": c.get("examples") or [],
                })

    results = []
    for t in TARGETS:
        nt = norm(t)
        hits = []
        for c in concepts:
            nc = norm(c["term"])
            blob = norm(c["definition"]) + norm("".join(c["keywords"])) + norm("".join(c["examples"]))
            s = 0
            if nc == nt:
                s = 100
            elif nt and nt in nc:
                s = 88
            elif nc and nc in nt and len(nc) >= 2:
                s = 80
            elif nt and nt in blob:
                s = 60
            if s:
                hits.append((s, c))
        hits.sort(key=lambda x: -x[0])
        results.append({"target": t, "hits": [dict(h) | {"score": h[0]} if False else {"score": h[0], **h[1]} for h in hits[:3]]})

    with open(os.path.join(OUT, "扩充候选.json"), "w", encoding="utf-8") as f:
        json.dump({"targets": results}, f, ensure_ascii=False, indent=1)

    ok = [r for r in results if r["hits"] and r["hits"][0]["score"] >= 80]
    weak = [r for r in results if r["hits"] and 60 <= r["hits"][0]["score"] < 80]
    none = [r for r in results if not r["hits"]]
    print("目标 %d 个：强匹配 %d / 弱匹配 %d / 无匹配 %d" % (len(TARGETS), len(ok), len(weak), len(none)))
    print()
    print("无匹配（三本书没有，需剔除）：")
    print("  " + "、".join(r["target"] for r in none))
    print()
    print("弱匹配（可能是误匹配，谨慎用）：")
    for r in weak:
        h = r["hits"][0]
        print("  %-16s -> [%s P%s] %s" % (r["target"], h["book"], h["page"], h["term"]))

    lines = ["# 扩充候选（原书段落）", ""]
    for r in results:
        if not r["hits"]:
            continue
        lines.append("## %s" % r["target"])
        for h in r["hits"]:
            lines.append("- score=%s [%s P%s | %s | %s] **%s**：%s" % (
                h["score"], h["book"], h["page"], h["chapter"][:16], h["section"][:36], h["term"], h["definition"]))
        lines.append("")
    with open(os.path.join(OUT, "扩充候选.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print()
    print("已写出 verify/扩充候选.json 与 verify/扩充候选.md")


if __name__ == "__main__":
    main()
