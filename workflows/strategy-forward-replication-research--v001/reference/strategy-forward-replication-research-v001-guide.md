# 策略前瞻複製研究流程 v001

## 文件定位

本文件說明 `strategy-forward-replication-research--v001` 的操作方式。行為權威是同一 Workflow Package 內，由 `release-manifest.yml` 綁定的 `workflow.yml`、`rules/`、`schemas/`、`policies/`、`validator/` 與 `writer/`。本次 Lifecycle 調整已由 Trusted Approver `william` 於 2026-09-04 重新核准，現在可作為 active workflow 使用。正式研究不得使用 `--allow-draft` 規避 release 驗證。

## 結果能代表什麼

所有 outcome windows 都已結束。即使 Study 通過，也只得到 `retrospectively-supported`，不表示未來績效、Shadow 資格、broker authority 或實盤交易許可。
`pass` 只表示通過本 Workflow 定義的 Historical Evaluation；它不代表沒有執行的 robustness challenge、Replay 或其他外部檢查也已通過。

## Study 如何保存

每個 Study 位於：

```text
workflows/strategy-forward-replication-research--v001/studies/<study-id>/
```

`events/` 內的 canonical YAML Study Events 是唯一事實來源。每個 event 都引用前一個 event digest；`study.yml` 只是 writer 產生的 projection，刪除後可以重建，手動修改不會改變權威事實。

每次事件發布還會在設定的本機 authority root 追加 checkpoint。這套簡化機制用來發現誤刪、改寫、換序和意外回退；它不防止擁有檔案最高權限的人同時刪除 Study 與 authority records。

## 正式順序

```text
Study Created
→ Preregistration Approved
→ Development Authorized
→ Trials Recorded
→ Trial Registry Frozen
→ Provenance Audited
→ Candidate Frozen
→ Historical Evaluation Completed
→ Study Terminal
```

Historical Evaluation 完成後必須另以 `study-terminal` 事件結束 Study；Historical Evaluation 事件本身不等於終止。只有明確的提前終止路徑可以在更早階段進入 terminal。必要 evidence 在引用前就無法取得時，先記錄 `evidence-unavailable`，再以 `indeterminate` 終止；不能假裝該階段通過。可恢復技術中斷使用 `study-paused` 和 `study-resumed`，且只能恢復同一 frozen operation。

## Provenance

- `verified-clean`：可以繼續。
- `known-contaminated`：終止為 `fail`。
- `provenance-unknown`：終止為 `indeterminate`。

人工核准不能覆蓋這個對應。

## Trial、Candidate 與 Baseline

Trial 由完整 outcome-relevant inputs 識別。完全相同 inputs 的技術重試仍是同一 Trial；任何會影響結果的 input 改變都建立新 Trial 並消耗 budget。失敗、移除和放棄但已查看結果的 Trials 仍永久保留。

Selected Candidate 必須來自完整 Candidate Family。Baseline 位於 Candidate Family 之外，且必須依 preregistration 中可檢查的規則來自不同、更簡單的 strategy family。

## Data Snapshots 與 folds

Warmup、Development、quarantine 與 Historical Evaluation 各有固定 Session Inventory。Validator 使用 XNYS calendar 重建預期 sessions，拒絕缺漏、額外、重複、錯序或角色重疊。較早 Study 可能保留 2025 Replay 的歷史欄位，但那不是目前 Lifecycle 的必要角色。

每個 Evaluation Fold 都重設 position、cash、cooldown 與 ledger。指標只使用該年度開頭固定 sessions 暖機；warmup 不產生 signals、trades 或 performance，也不承接前一年或 quarantine 狀態。最大持有期和 entry cutoff 必須在 preregistration 固定。

## Policies

本 Workflow Package 自帶四份 exact policy releases：

- `us-equity-market--v002`；
- `canonical-execution--v001`；
- `portfolio-risk--v001`；
- `paper-proposal-orders--v001`。

Proposal 只允許 `MARKET`、`LIMIT` 與 `STOP_MARKET`，而且全部 non-actionable。Formal runs 不得連線 market-data provider、broker 或建立真實 orders。

## Review

Validator 必須從 frozen raw evidence 重新計算 metrics 和 gates，不信任 caller-reported pass，也不能修改既有 evidence。Terminal Evidence 記錄這次重算結果與必要 digest，完成後才能追加 `study-terminal`；它是終止事件的佐證，不是另一個 post-evaluation stage。

## CLI

在 Workflow Package 目錄或把該目錄加入 Python path 後，可使用：

```text
python -m writer.cli --authority-root <authority-root> create ...
python -m writer.cli --authority-root <authority-root> append ...
python -m writer.cli --authority-root <authority-root> publish-artifact ...
python -m writer.cli --authority-root <authority-root> validate ...
python -m writer.cli --authority-root <authority-root> recover ...
```

`--allow-draft` 只供 tests 和 release preparation。正式 writer 沒有有效 `release.yml` 時會拒絕操作。

## Release 與後續修改

正式 release 必須具備可重算的 `release-manifest.yml` 與 `release-test-report.yml`，通過全部 tests 和 Ruff，並由 trusted approver 建立 `release.yml`。任何受 manifest 保護的規則、程式、測試或文件只要修改，就必須重新執行驗證、產生 manifest 與測試報告，再由 trusted approver 重新核准；不能沿用舊 release 宣稱修改後的內容仍已獲核准。
