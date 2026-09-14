#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成《核对报告.md》——把核对结果、新增条目、取题规则汇总成可读文档。"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(BASE, "题库.json")
OLD = os.path.join(BASE, "题库_核对前.json")
OUT = os.path.join(BASE, "核对报告.md")

VERDICT_CN = {"matched": "书证确凿", "partial": "部分对应", "not_in_books": "三书无对应"}


def main():
    bank = json.load(open(BANK, encoding="utf-8"))
    old = json.load(open(OLD, encoding="utf-8"))
    o = {i["seq"]: i for i in old["items"]}

    items = sorted(bank["items"], key=lambda x: x.get("seq", 0))
    verified = [i for i in items if i.get("seq") in o]
    added = [i for i in items if i.get("seq") not in o]

    from collections import Counter
    vc = Counter(i.get("verified", "?") for i in verified)
    nd = sum(1 for i in verified if i["definition"] != o[i["seq"]]["definition"])
    npt = sum(1 for i in verified if i["points"] != o[i["seq"]]["points"])

    L = []
    L.append("# 名词解释题库 · 原文核对报告")
    L.append("")
    L.append("核对日期：2026-09-14　｜　核对依据：三本教材全量逐页阅读笔记（915 页 / 2560 条概念）")
    L.append("")
    L.append("## 一、核对怎么做的")
    L.append("")
    L.append("三本书都是**无文本层的扫描件**（彭吉象《艺术学概论》第 6 版 460 页、钟大丰舒晓鸣《中国电影史》232 页、"
             "郑亚玲胡滨《外国电影史》223 页）。本机三套 OCR 引擎均不可用（tesseract 装不上、onnxruntime 动态库不兼容），"
             "因此改为**把每一页渲染成图、逐页视觉阅读**，把概念名、书中原句定义、关键词、例子、章节位置全部落到结构化笔记里，"
             "再用这份笔记去逐条比对题库。")
    L.append("")
    L.append("比对过程：先按名词做关键词匹配抽出候选原文段落，再逐条判断该段落是否真的在讲这个概念"
             "（初筛的误匹配率不低，例如「汉画像石」会匹配到「雕塑的各种技艺」），只有确实对应的才用作书证。")
    L.append("")
    L.append("## 二、核对结论")
    L.append("")
    L.append("| 项目 | 数量 |")
    L.append("|---|---|")
    L.append("| 原有条目 | %d |" % len(verified))
    L.append("| 其中：书证确凿（定义按原书原句改写，标注到页码） | %d |" % vc.get("matched", 0))
    L.append("| 其中：部分对应（书中有相关内容，但无定义性表述） | %d |" % vc.get("partial", 0))
    L.append("| 其中：三书均无对应表述（保留原答案，如实标注依据） | %d |" % vc.get("not_in_books", 0))
    L.append("| 定义被改写 | %d |" % nd)
    L.append("| 答题要点被调整 | %d |" % npt)
    L.append("| 出处标注全部重写（去掉了「[补] 待核实」） | %d |" % len(verified))
    L.append("| 新增补充条目（全部依据教材原文撰写） | %d |" % len(added))
    L.append("| 题库总量 | %d |" % len(items))
    L.append("")
    L.append("**出处标注的两种写法**，可以据此判断每条答案的可信度：")
    L.append("")
    L.append("- `[艺术学概论] P385（第十一章第二节），原文核对通过` —— 已逐字比对该页原文，定义以原书原句为核心。")
    L.append("- `三本教材均无对应表述，依据 zhenti.md 真题及学科通识，未逐字核对` —— 这三本书确实没讲，"
             "答案来自真题与学科通识，**未逐字核对，请以课堂笔记／其他专著为准**。")
    L.append("")
    L.append("## 三、逐条核对结果")
    L.append("")
    L.append("### 原 90 条")
    L.append("")
    L.append("| 序 | 名词 | 判定 | 出处标注 |")
    L.append("|---|---|---|---|")
    for i in verified:
        sn = i["source_note"].replace("|", "／")
        L.append("| %s | %s | %s | %s |" % (i["seq"], i["term"], VERDICT_CN.get(i.get("verified"), "?"), sn))
    L.append("")
    L.append("### 新增 %d 条（均依据教材原文）" % len(added))
    L.append("")
    L.append("| 序 | 名词 | 依据 | 出处 |")
    L.append("|---|---|---|---|")
    for i in added:
        L.append("| %s | %s | %s | %s |" % (i["seq"], i["term"], i.get("src_book", ""), i["source_note"]))
    L.append("")
    L.append("## 四、每天推什么（取题规则）")
    L.append("")
    L.append("按「真题有限，不要一天全是真题」的要求，改成 **每期 1 道真题 + 4 道补充**，真题夹在第 3 题的位置：")
    L.append("")
    L.append("- 真题池 %d 条（2020–2025 真题原词），每天 1 道 → 29 天一轮" % len([i for i in items if i.get("track") == "真题"]))
    L.append("- 补充池 %d 条（教材概念 + 真题衍生概念 + 新增教材条目），每天 4 道 → 116 ÷ 4 = 29 天一轮" % len([i for i in items if i.get("track") != "真题"]))
    L.append("- 两池**同步 29 天一轮**，一轮之内 145 道题**不重复**；第 30 天自动从第 1 题开始二刷")
    L.append("- 补充池的次序用固定随机种子打乱，教材概念、电影史条目交替出现，避免连着几天同一个方向")
    L.append("- 推送正文与答题页用**同一套取题算法**（已逐日比对 40 天，完全一致）")
    L.append("")
    L.append("## 五、已知局限（请知悉）")
    L.append("")
    L.append("1. **%d 条没有教材书证**：这些是美术史、文学史、当代电影理论等超出三本书范围的概念"
             "（如汉画像石、宝莱坞、《闲情偶寄》、凝视理论、第三电影）。答案来自通识与真题资料，已如实标注；"
             "若要达到「逐字有出处」，需要补对应学科教材（中外美术史、文学史、电影理论读本），你给我书我就继续核。" % vc.get("not_in_books", 0))
    L.append("2. **视觉读页不是 OCR**：书中个别字词可能有识别偏差，引用原文时以书页为准。抽查中已修正多处，"
             "但如果你在某条答案里看到可疑表述，挑出来我回原书核对。")
    L.append("3. **真题池只够 29 天一轮**：真题原词满打满算就这些，二刷对考研是好事，但若想一直不重复，需要继续扩池。")
    L.append("")
    L.append("## 六、可复现的脚本")
    L.append("")
    L.append("```")
    L.append("scripts/build_worksheet.py    # 用全书笔记为题库生成「核对工作单」（含候选原文）")
    L.append("scripts/merge_verify.py       # 合并核对结果 + 校验页码真伪，写出题库")
    L.append("scripts/patch_manual.py       # 人工审校补丁（定义过短的条目补足）")
    L.append("scripts/find_expansion.py     # 从全书笔记里检索新条目的候选原文")
    L.append("scripts/plan_expansion.py     # 生成扩充任务单（55 个名词）")
    L.append("scripts/merge_expansion.py    # 合并扩充结果 + 校验")
    L.append("scripts/build_cycle.py        # 打上「真题/补充」双池轨道与固定顺序位")
    L.append("```")
    L.append("")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("已生成 %s（%d 行）" % (os.path.basename(OUT), len(L)))


if __name__ == "__main__":
    main()
