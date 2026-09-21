---
name: run-strategy-historical-evaluation-v004
description: 由 Study 歷史評估執行者對已 frozen 的 v004 Study 執行唯一 Historical Evaluation 至 terminal；不建立或調整策略。
---

# v004 Historical Evaluation

目前角色必須是 **Study 歷史評估執行者**，不得自行切換成 study 開發者或 blind reviewer。只接受單一 v004 Study 的明確 `historical-evaluation-to-terminal` 派工，而且 candidate 必須已 frozen；正式操作必須有有效 Workflow Release，不得用 `--allow-draft`。

先讀 `AGENTS.md` 與 `workflows/strategy-forward-replication-research--v004/reference/operations.md`。在讀取 evaluation data 前，先由 v004 CLI 驗證 `manifests/workflow-reference.yml`、release manifest、release record、policy set、candidate freeze、source bundle、runner、plan 與資料 digest。

固定使用：

```bash
python workflows/strategy-forward-replication-research--v004/operations/cli.py \
  --repository-root <repo> --authority-root <authority> \
  --role 'Study 歷史評估執行者' historical-evaluation <study-id> \
  --plan <evaluation-plan> --assignment <assignment>
```

Historical Evaluation 只能執行一次。reservation、started event、authority／local launch marker 與 runtime manifest 都由 CLI 建立；執行 workspace 是暫存目錄，Study operation 不得留下 `runtime/workflow/`，正式結果只能由 writer 寫入 `historical-evaluation-artifacts/<Study-ID>/`。輸出缺失或 marker 已存在時，保守產生 `indeterminate`，不得刪 marker、換 candidate、換 reference 或重新 launch。

中斷時只用原派工與原 operation 執行 `resume`；不得手動修補事件、terminal、evidence、runtime manifest 或 authority。不得調整策略、門檻、candidate、資料區間，也不得讀取或撰寫 blind review／Development note。完成 terminal 後停止並回報 operation ID、reference digest、evidence digest、outcome 與 recovery 狀態。
