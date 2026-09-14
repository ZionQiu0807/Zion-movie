#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键部署到 GitHub：建仓库 → 推送代码 → 写入 Secrets → 开启 Pages。

用法（token 从环境变量读，避免出现在命令历史里）：
    GH_TOKEN=ghp_xxx python scripts/deploy_github.py --repo Zion-movie

需要 classic PAT，勾选 repo + workflow 两个 scope。
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def api(method, path, token, body=None, ok=(200, 201, 204)):
    url = path if path.startswith("http") else API + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "bfa-mingci-deploy",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8")
            return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        if e.code in ok:
            return e.code, (json.loads(raw) if raw.strip() else {})
        raise RuntimeError("GitHub API %s %s 失败：HTTP %d\n%s" % (method, path, e.code, raw[:600]))


def git(*args, env=None, check=True):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(["git"] + list(args), cwd=BASE, env=e,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise RuntimeError("git %s 失败：\n%s\n%s" % (" ".join(args), p.stdout, p.stderr))
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="Zion-movie")
    ap.add_argument("--private", action="store_true", help="默认公开（Pages 免费版需要）")
    ap.add_argument("--skip-pages", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("GH_TOKEN")
    if not token:
        print("错误：请设置环境变量 GH_TOKEN")
        return 2

    status, user = api("GET", "/user", token)
    owner = user["login"]
    repo = args.repo
    print("[1/6] 已认证为：%s" % owner)

    # --- 2. 建仓库（已存在则复用）---
    try:
        status, r = api("GET", "/repos/%s/%s" % (owner, repo), token)
        print("[2/6] 仓库已存在，复用：%s" % r["html_url"])
    except RuntimeError:
        status, r = api("POST", "/user/repos", token, {
            "name": repo,
            "description": "北电考研专业一 名词解释每日五题 · 微信定时推送",
            "private": bool(args.private),
            "has_issues": False,
            "has_wiki": False,
            "has_projects": False,
        })
        print("[2/6] 已创建仓库：%s" % r["html_url"])

    clone_url = "https://github.com/%s/%s.git" % (owner, repo)

    # --- 3. 推送代码（token 只用于这一次 push，不写入 .git/config）---
    auth_url = "https://x-access-token:%s@github.com/%s/%s.git" % (token, owner, repo)
    git("remote", "remove", "origin", check=False)
    git("remote", "add", "origin", clone_url)
    p = git("push", auth_url, "main:main", "--force", check=False)
    if p.returncode != 0:
        # 空仓库首次推送可能被拒，重试普通推送
        p = git("push", "-u", auth_url, "main", "--force", check=False)
    if p.returncode != 0:
        raise RuntimeError("推送失败：\n%s\n%s" % (p.stdout, p.stderr))
    print("[3/6] 代码已推送（remote: %s）" % clone_url)

    # --- 4. 写 Secret：PUSHPLUS_TOKEN ---
    pushplus = None
    cfg_local = os.path.join(BASE, "config.local.json")
    if os.path.exists(cfg_local):
        pushplus = json.load(open(cfg_local, encoding="utf-8")).get("pushplus_token")
    if not pushplus:
        print("[4/6] 跳过：config.local.json 里没找到 pushplus_token")
    else:
        status, key = api("GET", "/repos/%s/%s/actions/secrets/public-key" % (owner, repo), token)
        from nacl import encoding, public
        pk = public.PublicKey(key["key"].encode("utf-8"), encoding.Base64Encoder())
        sealed = base64.b64encode(public.SealedBox(pk).encrypt(pushplus.encode("utf-8"))).decode("utf-8")
        api("PUT", "/repos/%s/%s/actions/secrets/PUSHPLUS_TOKEN" % (owner, repo), token,
            {"encrypted_value": sealed, "key_id": key["key_id"]})
        print("[4/6] 已写入 Secret：PUSHPLUS_TOKEN（值已加密，仓库内不可见）")

    # --- 5. 开启 GitHub Pages（main 分支 /docs）---
    pages_url = None
    if not args.skip_pages and not args.private:
        body = {"source": {"branch": "main", "path": "/docs"}}
        try:
            status, pg = api("POST", "/repos/%s/%s/pages" % (owner, repo), token, body,
                             ok=(201, 409, 422))
            if status in (409, 422):
                status, pg = api("PUT", "/repos/%s/%s/pages" % (owner, repo), token, body)
            pages_url = pg.get("html_url") or ("https://%s.github.io/%s/" % (owner, repo))
            print("[5/6] 已开启 Pages：%s" % pages_url)
        except RuntimeError as e:
            print("[5/6] 开启 Pages 失败（可稍后在 Settings → Pages 手动开）：%s" % str(e)[:300])
    else:
        print("[5/6] 跳过 Pages")

    # --- 6. 触发一次 Actions，预览内容（dry_run）---
    try:
        api("POST", "/repos/%s/%s/actions/workflows/daily_push.yml/dispatches" % (owner, repo),
            token, {"ref": "main", "inputs": {"date": "", "dry_run": "1"}})
        print("[6/6] 已触发一次预览运行（dry_run），去 Actions 页面看结果")
    except RuntimeError as e:
        print("[6/6] 触发 Actions 失败（不影响已完成的配置）：%s" % str(e)[:300])

    print("\n完成。仓库：%s" % r["html_url"])
    if pages_url:
        print("答题页：%s" % pages_url)
    print("Actions：https://github.com/%s/%s/actions" % (owner, repo))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as e:
        print("\n" + str(e))
        raise SystemExit(1)
