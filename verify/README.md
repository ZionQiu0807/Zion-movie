# verify/ · 核对与扩充的过程文件

| 文件 | 说明 |
|---|---|
| `核对结果_批次01..06.json` | 原 90 条题库的逐条核对结论（定义、要点、出处、判定、改动说明），由 `scripts/merge_verify.py` 合并回 `题库.json` |
| `扩充结果_批次01..04.json` | 新增 55 条补充条目的撰写结果，由 `scripts/merge_expansion.py` 合并回 `题库.json` |

其余文件（`核对工作单*`、`扩充候选*`、`扩充工作单*`、`扩充选中.json`、渲染用的 jpeg）
是生成过程中的中间产物，体积较大，未纳入版本管理；需要时用下列脚本重新生成：

```bash
python scripts/build_worksheet.py    # 生成核对工作单（含候选原文段落）
python scripts/find_expansion.py     # 生成扩充候选（含候选原文段落）
python scripts/plan_expansion.py     # 生成扩充任务单
```
