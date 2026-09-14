# -*- coding: utf-8 -*-
"""把三本扫描 PDF 渲染为图片，供视觉阅读/核实答案使用。"""
import os, sys, time, json
import pymupdf

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_BASE = os.path.join(BASE, "book_images")

BOOKS = [
    {
        "name": "艺术学概论",
        "pdf": r"C:/Users/silen/WorkBuddy/2026-08-27-14-33-57/kaoyan/彭吉象艺术学概论/《艺术学概论第六版》彭吉象.pdf",
        "dpi": 170,
    },
    {
        "name": "中国电影史",
        "pdf": r"C:/Users/silen/WorkBuddy/2026-08-27-14-33-57/kaoyan/中国电影史/《中国电影史》钟大丰、舒晓鸣.pdf",
        "dpi": 170,
    },
    {
        "name": "外国电影史",
        "pdf": r"C:/Users/silen/WorkBuddy/2026-08-27-14-33-57/kaoyan/外国电影史/《外国电影史》郑亚玲、胡滨.pdf",
        "dpi": 170,
    },
]

def render(book):
    pdf = book["pdf"]
    name = book["name"]
    dpi = book["dpi"]
    out = os.path.join(IMG_BASE, name)
    os.makedirs(out, exist_ok=True)

    print(f"[{name}] 开始渲染 -> {out}", flush=True)
    t0 = time.time()
    doc = pymupdf.open(pdf)
    meta = {"name": name, "pages": doc.page_count, "dpi": dpi, "dir": out, "files": []}
    for i in range(doc.page_count):
        page = doc[i]
        pix = page.get_pixmap(dpi=dpi)
        fn = os.path.join(out, f"page_{i+1:04d}.jpg")
        pix.save(fn, jpg_quality=85)
        meta["files"].append({"page": i + 1, "file": fn, "w": pix.width, "h": pix.height})
        if (i + 1) % 20 == 0:
            print(f"[{name}] {i+1}/{doc.page_count} ({(i+1)/doc.page_count:.0%})", flush=True)
    doc.close()
    meta["elapsed"] = round(time.time() - t0, 2)
    meta["bytes"] = sum(os.path.getsize(f["file"]) for f in meta["files"])
    meta_json = os.path.join(out, "meta.json")
    json.dump(meta, open(meta_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[{name}] 完成：{len(meta['files'])} 页，耗时 {meta['elapsed']}s，共 {meta['bytes']/1024/1024:.1f} MB", flush=True)
    return meta

if __name__ == "__main__":
    total_t0 = time.time()
    all_meta = []
    for b in BOOKS:
        all_meta.append(render(b))
    summary = os.path.join(IMG_BASE, "summary.json")
    json.dump({"books": all_meta, "total_time": round(time.time() - total_t0, 2)},
              open(summary, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n全部渲染完成。汇总:", summary)
