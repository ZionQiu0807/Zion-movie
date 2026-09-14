# 每日名词解释 · 专业一

每天 12:30 自动推送 5 道北京电影学院考研专业一（艺术基础理论）名词解释到微信，点开链接做题、点题目才展开答案。

链路完全跑在云端，**不需要本机开机、不需要 WorkBuddy 运行**：

```
GitHub Actions（每天 12:30 北京时间）
    └── 运行 push.py，读 题库.json 算出当天 5 题
            └── 调 PushPlus HTTP 接口 → 微信收到消息
                    └── 消息里的链接指向 GitHub Pages 答题页（按日期自动取题）
```

## 配置说明（本仓库已完成，重建时参考）

> 以下步骤已由 `scripts/deploy_github.py` 自动完成。手动重建新仓库时按此操作。

### 1. 仓库设置

- 仓库需为 **Public**（GitHub Pages 免费版要求；私有仓库需 Pro 才能开 Pages）
- **Settings → Pages**：Source 选 `Deploy from a branch`，Branch 选 `main`，目录选 `/docs`
- 答题页地址即 `https://<用户名>.github.io/<仓库名>/`

### 2. Secrets

**Settings → Secrets and variables → Actions → New repository secret**

| 名称 | 值 | 必填 |
|---|---|---|
| `PUSHPLUS_TOKEN` | 你的 PushPlus token | 是 |

可选 Variable（**Settings → Secrets and variables → Actions → Variables**）：

| 名称 | 用途 |
|---|---|
| `SITE_URL` | 覆盖消息里的答题页链接（默认读 `config.json` 的 `site_url`） |

### 3. 验证

**Actions → 每日名词解释推送 → Run workflow**，`dry_run` 填 `1` 先预览内容，确认无误后不填再跑一次，微信应收到消息。

## 本地测试

```bash
python push.py --dry-run              # 只看内容不发送
python push.py                        # 推送今天
python push.py --date 2026-09-15      # 推送指定日期
```

本地 token 放在 `config.local.json`（已 gitignore）：

```json
{ "pushplus_token": "你的 token" }
```

优先级：环境变量 `PUSHPLUS_TOKEN` > `config.local.json` > `config.json`。

## 修改题库

1. 编辑 `题库.json`
2. 运行 `python build_site.py` 重新生成 `docs/`（答题页）与 `site/`
3. `git commit && git push` —— Pages 会自动更新，无需其他操作

`push.py` 与答题页使用同一套按日期取题算法（`start = (第n天 × 每天题数) mod 题库总数`），
所以只要 `题库.json` 与 `docs/data.js` 同步重建，微信里列的题目和页面上显示的必然一致。

> ⚠️ 改动题库顺序或总数会让**已推送过的历史期数**对应的题目发生变化。
> `题库.json` 里 `seq` 是固定序号，`shuffle_items.py` 用固定种子打乱，可复现。

## 注意事项

- **GitHub 定时任务在高峰期会延迟**几分钟到几十分钟，属正常现象，不影响当天题目。
- **仓库连续 60 天无提交，GitHub 会自动暂停 scheduled workflow**。偶尔提交一次即可恢复（或在 Actions 页面手动 Re-enable）。
- `cron` 用的是 UTC：`30 4 * * *` = 北京时间 12:30。
- 定时任务跑的是 UTC 时钟，脚本内部按**北京时间**取日期，避免延迟跨日导致推错期数。

## 文件说明

| 文件 | 用途 |
|---|---|
| `题库.json` | 题库唯一数据源（含定义、答题要点、记忆锚点、出处） |
| `push.py` | 算出当天 5 题 → 组装消息 → 调 PushPlus 发送 |
| `build_site.py` | 由题库生成答题页（`docs/` 与 `site/`） |
| `docs/` | GitHub Pages 发布目录 |
| `site/` | 同一份页面的副本，供 WorkBuddy 应用发布使用 |
| `config.json` | 非敏感配置（不含密钥，可提交） |
| `config.local.json` | 本地 token（**不提交**） |
| `notes/` | 三本教材全量读书笔记（915 页 / 2560 条概念），用于核对答案 |
| `shuffle_items.py` | 固定种子打乱题库顺序 |

## 答题页

- **云端（主）**：https://zionqiu0807.github.io/Zion-movie/
- 本地链路（备）：https://39795299112b40cf9adf07efaa5d0445.app.workbuddy.host

页面会根据打开日期自动显示当天 5 题，支持 `?d=YYYY-MM-DD` 查看指定日期。

## 当前部署状态

| 项目 | 值 |
|---|---|
| 仓库 | https://github.com/ZionQiu0807/Zion-movie （Public） |
| Actions | https://github.com/ZionQiu0807/Zion-movie/actions |
| Pages | `main` 分支 `/docs` 目录 |
| Secret | `PUSHPLUS_TOKEN`（已加密写入，仓库内不可见） |
| 定时 | 每天北京时间 12:30（UTC `30 4 * * *`） |

部署脚本：`scripts/deploy_github.py`（幂等，可重复执行）。

**本机定时任务已停用**（保留未删除，作回滚备份）：
- WorkBuddy automation `dc0c10fe-b291-436f-ad3b-0a0dabf703e3` → PAUSED
- Windows 计划任务 `BFA_Daily_Mingci_Push` → Disabled

恢复方式：automation 改回 ACTIVE；计划任务用 `Enable-ScheduledTask -TaskName "BFA_Daily_Mingci_Push"`。
**注意**：三者的触发时间都是 12:30，同时开启会重复推送。
