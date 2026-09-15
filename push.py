#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日推送：按日期算出当天 5 题，通过 PushPlus 推到微信。

本地运行：直接执行 push.py，token 从 config.json 读取。
GitHub Actions：设置 Secrets PUSHPLUS_TOKEN，脚本会自动用环境变量覆盖本地配置。

用法:
  python push.py                 # 推送今天的
  python push.py --date 2026-09-15
  python push.py --dry-run       # 只打印内容不发送
  python push.py --force         # 当天已推送过也强制重发
"""
import argparse
import datetime
import json
import os
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(BASE, "题库.json")
CONFIG = os.path.join(BASE, "config.json")            # 非敏感，随仓库提交
CONFIG_LOCAL = os.path.join(BASE, "config.local.json")  # 含 token，不提交
LOGDIR = os.path.join(BASE, "logs")
API = "http://www.pushplus.plus/send"

# 北京时间：GitHub runner 用 UTC，直接取本地日期在任务延迟时有跨日风险
TZ_BJ = datetime.timezone(datetime.timedelta(hours=8))

DEFAULTS = {
    "site_url": "https://39795299112b40cf9adf07efaa5d0445.app.workbuddy.host",
    "start_date": "2026-09-14",
    "per_day": 5,
    "channel": "wechat",
    "topic": None,
}


def load():
    cfg = dict(DEFAULTS)
    for path in (CONFIG, CONFIG_LOCAL):
        if os.path.exists(path):
            try:
                cfg.update(json.load(open(path, encoding="utf-8")))
            except Exception as e:
                print("警告：读取 %s 失败（%s），继续使用已有配置" % (path, e))
    # 环境变量优先级最高（GitHub Actions 走这条）
    for env_key, cfg_key in (("PUSHPLUS_TOKEN", "pushplus_token"),
                             ("SITE_URL", "site_url"),
                             ("START_DATE", "start_date"),
                             ("PER_DAY", "per_day")):
        v = os.environ.get(env_key)
        if v:
            cfg[cfg_key] = int(v) if cfg_key == "per_day" else v
    bank = json.load(open(BANK, encoding="utf-8"))
    return cfg, bank


def two_pools(bank):
    """真题池 / 补充池，各自按固定顺序位排列。"""
    zhenti = sorted([i for i in bank["items"] if i.get("track") == "真题"],
                    key=lambda x: x.get("zhenti_pos", 10**9))
    buchong = sorted([i for i in bank["items"] if i.get("track") != "真题"],
                     key=lambda x: x.get("buchong_pos", 10**9))
    return zhenti, buchong


def pick(bank, day, start_date, per_day):
    """当天题目：1 道真题 + (per_day-1) 道补充，真题夹在中间。

    两池各自循环，轮长一致（真题 29 / 补充 116÷4=29），一轮之内不重复。
    """
    d = datetime.date(*map(int, day.split("-")))
    s = datetime.date(*map(int, start_date.split("-")))
    n = (d - s).days
    zhenti, buchong = two_pools(bank)
    per_b = max(per_day - 1, 0)

    items = []
    if buchong and per_b:
        bs = ((n * per_b) % len(buchong) + len(buchong)) % len(buchong)
        items = [buchong[(bs + i) % len(buchong)] for i in range(per_b)]
    if zhenti:
        z = zhenti[(n % len(zhenti) + len(zhenti)) % len(zhenti)]
        items.insert(len(items) // 2, z)

    round_no = n // max(len(zhenti), 1) + 1
    return items, n + 1, round_no


def build_markdown(day, items, url, idx, round_no):
    lines = ["**%s · 专业一名词解释 %d 题**" % (day, len(items)), ""]
    for i, it in enumerate(items, 1):
        ys = it.get("years", [])
        if it.get("track") == "真题":
            mark = " ★真题%s" % (" " + "/".join(ys) if ys else "")
        elif it.get("origin") == "真题隐含":
            mark = " · 真题衍生%s" % ("（%s）" % ys[0] if ys else "")
        else:
            mark = " · 教材"
        lines.append("%d. **%s**%s" % (i, it["term"], mark))
    lines += ["",
              "[点这里做题 → 点题目展开答案](%s)" % url, "",
              "第 %d 期 · 第 %d 轮 · 每期 1 道真题 + 4 道补充 · 答不出的当天背熟" % (idx, round_no)]
    return "\n".join(lines)


def log_path():
    return os.path.join(LOGDIR, "推送记录.jsonl")


def already_pushed(day):
    """推送记录里是否已有该日期且成功的记录（用于定时任务延迟补跑去重）。"""
    p = log_path()
    if not os.path.exists(p):
        return False
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("date") == day and rec.get("code") == 200:
                    return True
    except Exception:
        return False
    return False


def send(token, title, content, channel, topic):
    payload = {"token": token, "title": title, "content": content,
               "template": "markdown", "channel": channel}
    if topic:
        payload["topic"] = topic
    req = urllib.request.Request(
        API, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="忽略当天已推送记录，强制再发一次")
    args = ap.parse_args()

    cfg, bank = load()
    day = args.date or datetime.datetime.now(TZ_BJ).date().isoformat()

    if not args.dry_run and not args.force and already_pushed(day):
        print(json.dumps({"date": day, "skipped": True,
                          "reason": "当天已成功推送过，跳过（如确需重发请加 --force）"},
                         ensure_ascii=False))
        return 0

    items, idx, round_no = pick(bank, day, cfg["start_date"], cfg["per_day"])
    md = build_markdown(day, items, cfg["site_url"], idx, round_no)
    title = "%s 专业一名词解释 %d 题" % (day, len(items))

    if args.dry_run:
        print(md)
        return 0

    token = cfg.get("pushplus_token")
    if not token:
        print("错误：未找到 PushPlus token。请设置环境变量 PUSHPLUS_TOKEN，"
              "或在项目根目录创建 config.local.json 写入 {\"pushplus_token\":\"...\"}")
        return 2

    res = send(token, title, md, cfg.get("channel", "wechat"),
               cfg.get("topic"))
    os.makedirs(LOGDIR, exist_ok=True)
    log = log_path()
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps({"date": day, "at": datetime.datetime.now(TZ_BJ).isoformat(timespec="seconds"),
                            "terms": [it["term"] for it in items],
                            "code": res.get("code"), "msg": res.get("msg")},
                           ensure_ascii=False) + "\n")
    print(json.dumps({"date": day, "terms": [it["term"] for it in items],
                      "pushplus_code": res.get("code"), "msg": res.get("msg")},
                     ensure_ascii=False, indent=2))
    return 0 if res.get("code") == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
