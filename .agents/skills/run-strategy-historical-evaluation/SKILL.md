---
name: run-strategy-historical-evaluation
description: 對 strategy-forward-replication-research--v001 中已完成 candidate freeze、尚未開始正式結果階段的單一 Study，執行一次性 2020--2024 Historical Evaluation、保存 immutable evidence，並完成其後的 Study Terminal。使用者明確要求執行或接續 Historical Evaluation 時使用；不建立或調整策略，也不執行 Historical Evaluation 以外的 challenge、replay 或 review。
---

# 執行 Historical Evaluation

這是一次性 outcome 操作。只在使用者明確要求執行、且指定一個 Study ID 或直接 Study 目錄時使用。

## 使用角色限制

- 本 skill 只能由 **Study 歷史評估執行者** 使用。
- 執行任何 preflight、讀取正式 Historical Evaluation 資料或發布結果前，必須確認目前對話角色就是 **Study 歷史評估執行者**。
- 其他角色不得以本 skill 執行 Historical Evaluation、讀取正式結果或發布相關 artifact；若目前角色不符，立即停止並說明角色限制。

## 強制 preflight

在讀取 Historical Evaluation 價格或執行策略前，先執行：

```bash
python3 .agents/skills/run-strategy-historical-evaluation/scripts/check_candidate_frozen.py <study-id-or-path>
```

只有輸出 `eligible` 且 exit code 0 才能繼續。檢查失敗時停止，不得自行建立 runner、回退事件、複製成新 Study 或用相似 Study 代替。

接著使用該 Study 原本的 authority root 執行 guarded writer `validate`。找不到或無法確認 authority root 時，先向使用者詢問；不得建立新的 authority history 來繞過驗證。

在開啟正式資料前再執行 gate-support preflight：

```bash
<project-python> .agents/skills/run-strategy-historical-evaluation/scripts/recompute_historical_evaluation.py <study-id> --check-gates-only
```

若任何 preregistered gate 不是 v001 validator 能產生的 metric，立即停止。Candidate freeze 後不得改名、移除或替換 gate。

## 執行前不變條件

- 事件鏈最後一個事件必須恰為 `000007-candidate-frozen.yml`，不得已有 `000008-*`。
- Source Bundle、candidate、qualification spec、snapshot set、fold inventory、selection evidence 與所有檔案 digest 必須吻合。
- 優先使用 Source Bundle 內已凍結且 digest 吻合的 `run_historical_evaluation.py`。若舊 Study 沒有 frozen runner，preflight 必須回傳 `adapter-required`，並在開啟正式資料前建立、合成測試及固定只負責 fold orchestration／evidence serialization 的 adapter；adapter 不得重寫或替代 frozen 策略規則。若做不到，停止。
- Preregistration 與 qualification spec 的 Evaluation gates 必須完全相同，且不得比 workflow floors 寬鬆。
- 正式 runner 不得連網，不得開啟 quarantine，不得修改程式、候選、成本、資料、fold、gate 或 entry cutoff。

## 一次性執行

開始正式 runner 前，在 commentary 明確告知使用者「即將揭露一次性 Historical Evaluation；開始後不能調參重跑」，但使用者的明確執行要求已是授權，不要再要求重複確認。

完整閱讀 [references/evaluation-method.md](references/evaluation-method.md)，嚴格依其 publication、重算及 recovery 流程執行。核心要求：

1. 只使用 frozen 2020--2024 evaluation snapshot 與 fold inventory。
2. 每個年度 fold 重設 portfolio 與策略狀態，只用 fold 內 warmup。
3. Runner 只產生 raw evidence，不以自報 pass/fail 取代 validator。
4. Evidence 產生後立即以新檔保存，不得覆寫；用 workflow validator 重算 metrics 和 gates。
5. 只經 guarded writer 發布 artifact、追加 `historical-evaluation-completed`，然後再次 validate。
6. 依 validator 重算的 disposition 產生 Terminal Evidence，再經 guarded writer 追加 `study-terminal`；Historical Evaluation 與 Study Terminal 是兩個不同事件。
7. 再次 validate，確認 Study 已 terminal；本 skill 不執行 robustness challenges、replay 或 Independent Review。

## 結果與停止條件

- `pass`：回報 Historical Evaluation 的 metrics、gate margins、evidence digest 與 Study Terminal event head；這只代表通過歷史評估，不代表其他未定義的穩健度或回放檢查。
- `fail`：保存並發布完整失敗 evidence，回報 failed gates，並以同一份重算結果完成 Study Terminal；不得改參數、換 runner 或重跑。
- 技術中斷：只允許同一 frozen operation、相同 inputs、runner digest 與已產生 bytes 的 recovery。不得刪除輸出後當成第一次執行。
- Evidence 或 identity 無法可信取得：依 workflow 記錄 `evidence-unavailable`／`indeterminate`；不要推測結果。

結尾明確列出實際讀取與發布的正式檔案，並聲明沒有執行 Historical Evaluation 以外的 challenge、replay 或 review。
