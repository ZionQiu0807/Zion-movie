#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 GitHub Git Data API 提交本地改动（一次请求生成一个提交）。

为什么不用 git push：本机 git 走沙箱代理时常被掐断（502 / unexpected disconnect），
而 REST API 一直稳定。流程：
  1. 用 git 算出相对 HEAD 的改动文件
  2. 逐个建 blob → 建 tree（base_tree 取远端当前 tree）→ 建 commit → 更新 ref
  3. 本地 git fetch + reset --hard 同步到新提交

用法：
  GH_TOKEN=xxx python scripts/api_commit.py "提交信息"
"""
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

OWNER = "ZionQiu0807"
REPO = "Zion-movie"
BRANCH = "main"


def api(method, path, body=None, token=None):
    url = "https://api.github.com" + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "User-Agent": "workbuddy-api-commit",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise RuntimeError("HTTP %s %s %s -> %s" % (e.code, method, path, detail[:400]))


def git(*args):
    return subprocess.run(["git"] + list(args), capture_output=True, text=True, check=True).stdout


def main():
    token = os.environ.get("GH_TOKEN")
    if not token:
        print("缺少 GH_TOKEN 环境变量")
        return 2
    msg = sys.argv[1] if len(sys.argv) > 1 else "更新题库与推送逻辑"

    # 先拿到远端当前提交，再据此计算本地有哪些文件不同
    ref = api("GET", "/repos/%s/%s/git/ref/heads/%s" % (OWNER, REPO, BRANCH), token=token)
    base_commit = ref["object"]["sha"]
    commit = api("GET", "/repos/%s/%s/git/commits/%s" % (OWNER, REPO, base_commit), token=token)
    base_tree = commit["tree"]["sha"]
    print("远端 HEAD：%s" % base_commit[:8])

    changes = []
    for line in git("diff", "--name-status", base_commit).splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0], parts[-1]
        changes.append((status[0], path))
    if not changes:
        print("与远端没有差异，无需提交")
        return 0
    print("待提交 %d 个文件：" % len(changes))
    for s, p in changes:
        print("  %s %s" % (s, p))

    entries = []
    for status, path in changes:
        full = os.path.join(os.getcwd(), path)
        if status == "D" or not os.path.exists(full):
            entries.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
            continue
        with open(full, "rb") as f:
            content = base64.b64encode(f.read()).decode("ascii")
        blob = api("POST", "/repos/%s/%s/git/blobs" % (OWNER, REPO),
                   {"content": content, "encoding": "base64"}, token=token)
        entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print("  blob %s %s" % (blob["sha"][:8], path))

    tree = api("POST", "/repos/%s/%s/git/trees" % (OWNER, REPO),
               {"base_tree": base_tree, "tree": entries}, token=token)
    new_commit = api("POST", "/repos/%s/%s/git/commits" % (OWNER, REPO),
                     {"message": msg, "tree": tree["sha"], "parents": [base_commit]}, token=token)
    api("PATCH", "/repos/%s/%s/git/refs/heads/%s" % (OWNER, REPO, BRANCH),
        {"sha": new_commit["sha"], "force": False}, token=token)
    print("已提交：%s" % new_commit["sha"][:8])

    # 本地同步
    try:
        git("fetch", "origin", BRANCH)
        git("reset", "--hard", "FETCH_HEAD")
        print("本地已同步到远端：%s" % git("log", "--oneline", "-1").strip())
    except subprocess.CalledProcessError as e:
        print("提示：本地同步失败（%s），可稍后手动 git fetch && git reset --hard FETCH_HEAD" % e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
