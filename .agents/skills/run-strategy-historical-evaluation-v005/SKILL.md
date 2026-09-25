---
name: run-strategy-historical-evaluation-v005
description: 由 Study 歷史評估執行者依明確 v005 派工，對已凍結的單一 Study 執行一次 Historical Evaluation 至 terminal；不建立或調整策略。
---

# v005 Historical Evaluation

## 角色與派工範圍

目前角色必須是 **Study 歷史評估執行者**，而且收到針對單一 v005 Study 的明確 `historical-evaluation-to-terminal` 派工。不得自行切換角色、開發或調整策略、改候選版本，或把含糊的「繼續研究」當成正式評估派工。candidate 必須已 frozen；沒有完成凍結就停止，不得代做 Development。

先讀 `AGENTS.md` 及下列 v005 契約，依它們判斷操作與資料界線：

- `workflows/strategy-forward-replication-research--v005/reference/operations.md`
- `workflows/strategy-forward-replication-research--v005/reference/workflow-reference.md`
- `workflows/strategy-forward-replication-research--v005/reference/multi-asset-input.md`
- `workflows/strategy-forward-replication-research--v005/schemas/assignment.schema.yml`
- `workflows/strategy-forward-replication-research--v005/schemas/evaluation-plan.schema.yml`
- `workflows/strategy-forward-replication-research--v005/schemas/data-snapshot-set.schema.yml`
- `workflows/strategy-forward-replication-research--v005/operations/cli.py`

派工紀錄須是符合 schema 的 canonical YAML，包含真實指令來源、原文或可追查摘錄、指派者、受派者、評估角色、Study ID、`workflow_version: v005` 及正確範圍。若明確指令已在目前任務中收到、但尚未保存派工，可依該指令建立紀錄；範例派工不可當成真實派工。v005 不要求另交簽名、核准人或核准時間，也不可加入核准欄位。派工本身不驗證指派者身分或指令真偽；不得把角色字串當成作業系統權限。

## 評估前檢查

正式評估一律使用 v005 CLI，並讓 CLI 在讀取 Study Source Bundle 或評估資料前驗證 Study 綁定的 `manifests/workflow-reference.yml`。reference 必須解析到 repository 內正確的 v005 Package，且 workflow、release manifest、正式 release record、Policy set digest 與 resolver version 都符合該 reference。路徑穿越、symlink escape、受限路徑、缺少正式 release 或任一 digest／版本不符時立即停止；不得改寫 reference、以目前版本覆蓋舊綁定，或使用 `--allow-draft` 繞過正式 release 檢查。

確認 Study 已 frozen，且評估計畫固定了凍結的 Historical Evaluation snapshot、runner contract、Source Bundle 與相同的候選版本。計畫的 `actor` 必須是 Study 指定的 `historical_evaluation_operator`，並與此評估派工的受派者一致。不得在評估中修改 candidate、來源、資料區間、runner、reference 或計畫指紋。若 CLI 回報缺件、資格失敗或綁定不符，停止並回報；不得手動補造證據。

評估計畫須包含 `actor`、`data_digest`，並且只能使用下列其中一種資料表示法：舊式單資產 `data_path`，或 v005 `data_assets`；不可同時使用。`data_digest` 必須等於凍結 snapshot 中 Historical Evaluation 資產清單的 canonical digest。多資產清單限 1–16 筆，按 `asset_id` 排序且不可重複，恰有一筆 `use: trade`，其他為 `reference`；每筆都須符合 Historical Evaluation 日期角色、紐約時區、收盤後可得時間及各自的資料 digest。每檔資料的日期清單必須一致且符合交易日規則；不得補值、插值、自動取交集，或在看到結果後更換資產。資料檔只由 CLI 依凍結輸入核對及讀取。

## 唯一評估操作與恢復

入口是 `workflows/strategy-forward-replication-research--v005/operations/cli.py`。全域參數放在子命令前，`--authority-root` 必須沿用 Study 原先綁定的 authority：

```sh
python workflows/strategy-forward-replication-research--v005/operations/cli.py \
  --repository-root <repo> --authority-root <原 authority> \
  --role 'Study 歷史評估執行者' \
  historical-evaluation <Study-ID> --plan <評估計畫.yml> --assignment <評估派工.yml>
```

一個 Study 只能有一次正式 Historical Evaluation。CLI 會在鎖內建立唯一 reservation、started event 與 checkpoint，並在啟動 runner 前保存 authority 及本地 launch marker。不可手動建立、刪除或修改這些記錄，也不可同時啟動多個評估。若已有 reservation、operation 或 marker，先用唯讀查詢掌握狀態；不得另換計畫再啟動第二次。

中斷時只可用原 Study、原派工及原 authority 對原 operation 執行 `resume`：

```sh
python workflows/strategy-forward-replication-research--v005/operations/cli.py \
  --repository-root <repo> --authority-root <原 authority> \
  --role 'Study 歷史評估執行者' resume <Study-ID> --assignment <原評估派工.yml>
```

已保存 reservation 但 started event 尚未完成時，恢復原事件；started 已完成而 launch marker 尚未建立時，CLI 可接續同一 operation。marker 已存在而輸出缺失或不完整時，結果必須是 `evidence-unavailable`／`indeterminate`，禁止重跑 runner。不得因中斷而刪 marker、改候選或資料、換 reference、重建 operation，或手動修補 event、terminal、evidence、journal、runtime manifest 與 authority。遇 `recovery-required`、`evaluation-already-started` 或不確定狀態時，依 CLI 的 recovery 資訊處理；無法由原 operation 安全恢復就停止並回報。

## Artifact 界線與完成回報

只有在目前明確派工指定該 Study 的 `historical-evaluation-to-terminal` 時，才能讀寫 `historical-evaluation-artifacts/<Study-ID>/`。不得遞迴列舉 artifacts 根目錄、讀取其他 Study 子目錄，或把結果複製到其他位置。正式 raw evidence 與 terminal evidence 只能由 v005 writer 以新檔案寫入指定子目錄；既有檔案不可覆寫或刪除。若發生檔名衝突或輸出不完整，不手動搬移、改名或清理，交由原 operation 的恢復流程處理。Study operation runtime 只保存 path／digest 引用，不保存 raw output，也不建立 `runtime/workflow/`。

terminal 完成後停止，回報 Study ID、operation ID、Workflow reference／release digest、evidence digest、terminal outcome 與恢復狀態。未完成或進入 `indeterminate` 時，清楚回報 CLI 的錯誤碼、缺少輸入與 `next_action`；不得宣稱評估成功或自行再跑一次。
