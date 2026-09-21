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

## 共用市場資料優先

- 市場資料是獨立於 Workflow 與 Source Bundle 的 immutable input。建立 Study 或準備 Development 時，先檢查 `research/market-data/yahoo/` 是否已有符合 ticker、日期範圍、欄位、XNYS、時區與 Yahoo `auto_adjusted` 規則的固定 snapshot 或 view；能直接 reference 就不要建立 Study-local CSV。
- 使用共用資料前，先讀取同名 `.quality.yml`，核對實際檔案的完整 repository-relative `data_path`、內容 SHA-256 `data_digest`、來源 snapshot、品質狀態與 session 範圍。檔名中的 digest 不能取代實際內容驗證；view 的 digest 也不能直接套用到其中的角色切片。
- `development` plan 與 `trial_inputs` 必須記錄實際使用的 `data_path`、`data_digest` 及 warmup／development role 的 digest；acquisition／lineage provenance 另記錄 source path、source digest、品質報告、session inventory 與 view 關係。
- Development 只能使用已授權的 warmup 與 development 區間，優先使用 `warmup-development` view。若因 runner 介面必須使用包含更大範圍的共用快照，`trial_inputs` 必須提供明確日期控制，且 runner 必須在策略程式讀取前限制可見資料；不得讓 Development 讀取 Historical Evaluation 的價格資料或結果。
- candidate freeze 仍須建立 `warmup-only`、`development`、`quarantine` 與 `historical-evaluation` 四個不重疊的 `data-snapshot-set` role entry。`warmup-development` view 只涵蓋前兩個 role，不能代替其餘 role，也不能從檔名或單一 view digest 推導缺少的 snapshot。
- 若沒有可直接解析的共用 view，先在 `research/market-data/yahoo/` 建立具固定檔名、品質報告與 digest 的 immutable role snapshot；只有 runner 無法解析共用 view 時，才使用 Study-local 副本，並在 provenance 記錄 fallback 原因。正式執行不得重新連線 Yahoo、下載新資料或追蹤會變動的 `latest` 檔案。

## 邊界

不得執行 `historical-evaluation`、讀取或寫入 `historical-evaluation-artifacts/`、修改 frozen candidate／門檻／Workflow Package，或手動建立事件、authority checkpoint、runtime manifest 與 evidence。發生中斷時只用同一 Study、同一派工與同一 operation resume；不要建立第二個 operation。

交接時回報 Study ID、`v004`、Workflow reference digest、source bundle digest、authority root、operation ID、事件 head、candidate freeze 狀態與缺件。完成 Development 後停止，不宣稱正式評估結果。
