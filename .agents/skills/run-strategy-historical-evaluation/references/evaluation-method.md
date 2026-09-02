# Historical Evaluation 執行方法

## 1. 凍結狀態稽核

先保存 writer `validate` 輸出中的 Study ID、event-chain head、candidate digest、qualification digest、Source Bundle digest、evaluation snapshot digest、fold inventory digest 與 authority root。

逐檔重算 Source Bundle SHA-256。確認 runner 是 Source Bundle 內的 repository path，且沒有 candidate freeze 後的修改。確認 research 與 Study ID 同名。

比較：

```python
assert qualification["evaluation"] == preregistration["evaluation_gates"]
```

再由 workflow floors 檢查 Study gate 沒有更寬鬆。這些檢查必須在正式價格被 runner 開啟前完成。

執行 `recompute_historical_evaluation.py <study-id> --check-gates-only`，確認每個 gate 都存在於 v001 `historical_metrics`。名稱近似不代表等價；unsupported gate 會讓正式 event 無法由 validator 判定，必須在此停止。

## 2. Runner 契約

優先使用 Source Bundle 凍結的 `run_historical_evaluation.py` 與它原本文件化的 CLI。合格 runner 必須接受 frozen evaluation snapshot 和 output path，並綁定 candidate、preregistration、qualification、snapshot set 與 Source Bundle identity。

舊 Study 沒有 frozen runner 時，可以在正式資料尚未開啟前建立 evaluation adapter，但必須同時滿足：

- 只匯入並呼叫 frozen strategy engine，不複製訊號、成交、成本、sizing 或退場規則；
- fold、warmup、reset、entry cutoff 與 evidence serialization 全部由 frozen manifests／workflow 讀入；
- adapter path、SHA-256、CLI 與合成 fold 測試結果在執行前保存；
- adapter 及其測試在正式執行前通過 Ruff 和 pytest；
- 最終報告揭露 adapter 未列於 candidate-freeze Source Bundle，不能誤稱為 frozen runner。

若 adapter 必須硬編碼或重新實作 candidate 規則才能工作，停止；這表示 Study 缺少可信的 execution identity。

Runner 應拒絕已存在的 output path。正式輸出先寫到 `research/<study-id>/historical-evaluation.raw.json` 或另一個明確、唯一且不覆寫的同名 operation path，再 canonicalize 成 `historical-evaluation.yml`。

若 frozen runner CLI 與 Source Bundle 文件不一致，停止；不要猜參數或修改 runner。

## 3. Fold 規則

固定使用五個 folds：2020、2021、2022、2023、2024。

- 每 fold 重設 cash、position、pending signal、cooldown、ledger 和 indicator state。
- 每 fold 前 `fold_warmup_sessions` 只能暖機；不得產生 signal、entry、exit 或績效。
- Signal、entry、exit 必須在同一 fold。
- 依 `maximum_holding_sessions` 設 entry cutoff，確保 position 能自然在 fold 內完成；不可為了年末強制平倉。
- Gap、stop/target 同觸、成本、整數股、借款限制及風險預算全部沿用 frozen candidate。
- Base 與 stress 的交易生命週期應一致；差異只來自 frozen cost／sizing 規則允許的部分。

## 4. Raw evidence 與權威重算

Raw artifact 必須符合 `schemas/historical-evaluation.schema.yml`，只保存 schema 允許的 initial cash、family-wise confidence、stress drawdown limit 與逐筆 trades。不要把 runner 產生的摘要當成權威。

Canonicalize 後執行：

```bash
<project-python> .agents/skills/run-strategy-historical-evaluation/scripts/recompute_historical_evaluation.py <study-id> <canonical-evidence>
```

以輸出的 `failures` 決定 event payload disposition。接著：

1. guarded writer `publish-artifact` 至 `evidence/historical-evaluation.yml`；
2. 產生只含 `artifact_path`、`artifact_digest`、`disposition` 的 canonical payload；
3. guarded writer 追加 `historical-evaluation-completed`；
4. guarded writer `validate`，確認 event count 8、current event 正確、重算 disposition 一致。

如果正式 artifact path 已存在，不得覆寫。先確認它是否為本次同一 operation 的 exact bytes；否則停止並調查。

## 5. Recovery

正式 runner 一旦成功產生 outcome bytes，Study 即受到結果資訊影響，即使後續 publish 或 event append 失敗也不能改策略後重跑。

- raw output 已存在：保留並核對 digest，只繼續 canonicalize／publish 相同內容。
- artifact 已發布但 event 未追加：引用同一 artifact digest 續作。
- journal 中斷：使用 writer `recover`。
- runner 在產生完整 outcome 前失敗：可以用完全相同 runner、inputs 與 operation identity 技術重試；不得修改程式或參數。
- 無法證明是否已產生或看過結果：停止並依 provenance／evidence-unavailable 規則處理。

## 6. 報告

回報 validator 重算的總交易數、base/stress return、PF、最大回撤、traded folds、正報酬 fold 比例、交易與獲利集中度、family-wise confidence 及所有 failed gates。不得只說 pass/fail。

明確記錄 runner、evaluation snapshot、raw evidence、canonical artifact、payload、event digest 和 authority validation。不得開啟或執行 challenge、quarantine 或 replay。
