# 每日名词解释 · 专业一

每天 12:30 自动推送 5 道北京电影学院考研专业一（艺术基础理论）名词解释到微信：**1 道真题 + 4 道补充**（真题夹在第 3 题），点开链接做题、点题目才展开答案。

题库已用三本教材的原文逐条核对过，详见 [`核对报告.md`](核对报告.md)。

链路完全跑在云端，**不需要本机开机、不需要 WorkBuddy 运行**：

```
GitHub Actions（每天 12:30 北京时间）
    └── 运行 push.py，按日期从双池算出当天 5 题
            └── 调 PushPlus HTTP 接口 → 微信收到消息
                    └── 消息里的链接指向 GitHub Pages 答题页（按日期自动取题）
```

## 取题规则

| 池子 | 条数 | 每天出 | 轮长 |
|---|---|---|---|
| 真题池（2020–2025 真题原词） | 29 | 1 道 | 29 天 |
| 补充池（教材概念 / 真题衍生 / 新增教材条目） | 116 | 4 道 | 29 天 |

两池**同步 29 天一轮**，一轮内 145 道题不重复；第 30 天自动二刷。
补充池次序用固定随机种子打乱（`scripts/build_cycle.py`），教材概念与电影史条目交替出现。
推送正文与答题页共用同一算法，改动后必须跑 `build_cycle.py` + `build_site.py` 并同时提交。

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

1. 编辑 `题库.json`（新增条目建议同时补 `origin`、`src_book`、`years`）
2. `python scripts/build_cycle.py` 重打双池轨道（新增条目必须重跑，否则不会被取到）
3. `python build_site.py` 重新生成 `docs/`（答题页）与 `site/`
4. `git commit && git push` —— Pages 会自动更新，无需其他操作

> ⚠️ 改动题库顺序或总数会让**已推送过的历史期数**对应的题目发生变化。
> `scripts/build_cycle.py` 里 `SEED = 20260914` 固定，重排可复现。

## 核对答案（用教材原文）

```bash
python scripts/build_worksheet.py    # 用 notes/ 的读书笔记为每条题目抽出候选原文
# 逐批核对后把结论写成 verify/核对结果_批次NN.json
python scripts/merge_verify.py       # 合并 + 校验（页码真伪、无书证却标注核对通过等）
python scripts/make_report.py        # 生成 核对报告.md
```

`notes/` 是三本教材全量逐页阅读的笔记（915 页 / 2560 条概念），定义均为**书中原句**，
所以「原文核对通过」的条目都有页码可查。

## 注意事项

- **GitHub 定时任务在高峰期会延迟**几分钟到几十分钟，属正常现象，不影响当天题目。
- **仓库连续 60 天无提交，GitHub 会自动暂停 scheduled workflow**。偶尔提交一次即可恢复（或在 Actions 页面手动 Re-enable）。
- `cron` 用的是 UTC：`30 4 * * *` = 北京时间 12:30。
- 定时任务跑的是 UTC 时钟，脚本内部按**北京时间**取日期，避免延迟跨日导致推错期数。
- 本机 `git push` 经沙箱代理时常断流，改用 GitHub Contents / Git Data API 提交（见 `scripts/api_commit.py`）。

## 文件说明

| 文件 | 用途 |
|---|---|
| `题库.json` | 题库唯一数据源（含定义、答题要点、记忆锚点、出处、双池轨道） |
| `push.py` | 算出当天 5 题（1 真题 + 4 补充）→ 组装消息 → 调 PushPlus 发送 |
| `build_site.py` | 由题库生成答题页（`docs/` 与 `site/`） |
| `docs/` | GitHub Pages 发布目录 |
| `site/` | 同一份页面的副本，供 WorkBuddy 应用发布使用 |
| `config.json` | 非敏感配置（不含密钥，可提交） |
| `config.local.json` | 本地 token（**不提交**） |
| `notes/` | 三本教材全量读书笔记（915 页 / 2560 条概念），核对答案的依据 |
| `核对报告.md` | 逐条核对结果：哪些有书证、哪些三本书没有、改了什么 |
| `题库_核对前.json` | 核对前的题库快照（用于对比改动） |
| `scripts/` | 核对、扩充、打轨道、生成报告、部署等脚本 |
| `verify/` | 核对中间产物（默认不入库，仅保留核对结果与任务单） |

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
