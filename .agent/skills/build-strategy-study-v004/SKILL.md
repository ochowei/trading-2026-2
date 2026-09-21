---
name: build-strategy-study-v004
description: 為 strategy-forward-replication-research--v004 建立或接續單一 Study，完成 Development 到 candidate freeze；只限 study 開發者，不執行正式 Historical Evaluation。
---

# v004 Study Development

目前角色必須是 **study 開發者**，不得自行切換成 Study 歷史評估執行者、blind reviewer 或超級管理者。只接受明確指定的單一 Study 與 `development-to-freeze` 派工；模糊或跨 Study 指令先停止。

## 固定入口

先讀根目錄 `AGENTS.md`、本 Workflow 的 `reference/operations.md`，再使用固定 v004 CLI：

```bash
python workflows/strategy-forward-replication-research--v004/operations/cli.py \
  --repository-root <repo> --authority-root <authority> \
  --role 'study 開發者' prepare <study-id> --report <report>
```

建立 Study 前必須先通過 `runner-preflight` 與 `prepare`。正式操作不得使用 `--allow-draft`；它只可用於隔離合成 fixture。建立與開發依序使用 `create`、`development` 或 `develop-to-freeze`，直到 candidate freeze 或合法的 Development terminal。

## Reference-first 與去重規則

- 在讀取研究資料、runner 或 source bundle 前，先解析並驗證 Study 的 `manifests/workflow-reference.yml`；核對 Workflow、release manifest、policy set 與 digest。
- Study 只保存 reference，不複製 `runtime/workflow/`。執行器可在受控暫存 workspace 複製唯讀 Workflow，但 operation 最後只能留下 `runtime/runtime-manifest.yml`、request、evidence 與必要 metadata。
- 不自行複製 validator、writer、schema 或 Workflow 文件；讓 v004 CLI 使用固定 package。
- Source Bundle 仍是 Study-specific 的 immutable binding；不要把策略程式、runner 或 Development data 當成共用 Workflow。

## 邊界

不得執行 `historical-evaluation`、讀取或寫入 `historical-evaluation-artifacts/`、修改 frozen candidate／門檻／Workflow Package，或手動建立事件、authority checkpoint、runtime manifest 與 evidence。發生中斷時只用同一 Study、同一派工與同一 operation resume；不要建立第二個 operation。

交接時回報 Study ID、`v004`、Workflow reference digest、source bundle digest、authority root、operation ID、事件 head、candidate freeze 狀態與缺件。完成 Development 後停止，不宣稱正式評估結果。
