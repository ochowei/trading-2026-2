# 新 Study 建立方法

## 1. 研究設計

先把上一輪觀察分成三類：已確認的規格／實作缺陷、Development 警訊、未驗證設計假說。流程缺陷可以一起修正；策略本身每輪只選一個可歸因的主要變更，除非多個條件在經濟機制上不可分割。

預先寫清楚 setup、trigger、決策與成交時間、stop、target、holding、gap、同 session 歧義、成本、position sizing、cooldown clock、Candidate Family、Trial budget、baseline、選擇規則及各階段 gates。

不要根據已看過的 Development 數值，把門檻設在剛好能通過的位置而不說明依據。沿用舊 Development 時，在 provenance 明確標示 `development-informed`。

## 2. 同名 research bundle 與資料

建立 `research/<study-id>/`。所有 data binding 都應指向這個同名目錄。Development runner 只可開啟 2013 warmup-only 與 2014--2018 Development。

Historical Evaluation、quarantine、replay 快照可以依 manifest 既有 digest 機械複製與 hash 驗證；不要輸出內容、統計或策略績效。不得連線 provider 更新正式資料。

## 3. Outcome-relevant 程式

不要修改已被其他 Study Source Bundle 凍結的檔案。新增獨立策略模組與測試，或在不影響舊 digest 的前提下重用既有模組。

Source Bundle 至少包含策略引擎、直接依賴、測試、Development runner、Historical Evaluation runner、preregistration、`pyproject.toml` 與 lockfile。

Historical Evaluation runner 必須在 freeze 前完成並用合成 folds 測試：

- 每個 2020--2024 fold 重設 cash、position、cooldown 與 ledger；
- 每年只用 fold 內前 N sessions 暖機，warmup 不可交易；
- signal、entry、exit 都落在同一 fold；
- entry cutoff 確保最大持有期能在 fold 內完成，不可強制年末退場；
- 只輸出 schema 允許的 raw trades 與 frozen constants，不自行宣告 metrics。

Runner 的 CLI 也要在檔案 docstring 或 `--help` 固定，至少明確接受 frozen evaluation snapshot 與不可覆寫的 output path，並能綁定 candidate definition、preregistration、qualification spec、snapshot set 與 Source Bundle identity。下一階段不得靠猜測參數或臨時修改 wrapper 才能執行。

## 4. Gate 單一來源檢查

在 preregistration 核准與 candidate freeze 前都重算：

```python
assert qualification["development"] == preregistration["eligibility_rules"]["development_gates"]
assert qualification["evaluation"] == preregistration["evaluation_gates"]
assert qualification["replay"] == preregistration["replay_gates"]
```

執行器產生的每個 Development gate 名稱、operator 與 required value也必須逐項相同。不得靜默新增 gate。

此外，逐一把 Evaluation 與 replay gate 名稱對照 `validator/artifacts.py` 實際產生的 metrics。v001 Historical Evaluation 的 drawdown metric 名稱是 `stress_max_drawdown`；不得使用看似合理但 validator 不會產生的別名，也不得在不更新並重新 release workflow validator 的情況下加入自訂正式 metric。Freeze 前應以空白合成 evidence 跑一次 validator gate-support preflight。

## 5. Development

在 preregistration-approved 與 development-authorized 後，按 Trial budget 執行。每個曾查看結果且 outcome-relevant inputs 不同的版本都是新 Trial。

Development evidence 至少保存 base/stress 逐筆交易、pre-entry equity 比例、主要 metrics、signal-year 分段、preregistered leave-one-year-out、block bootstrap、完整 gates、network access 與全部 frozen digests。由 raw trades 重算摘要，不信任 runner 自報 disposition。

## 6. Writer 事件鏈

只使用 workflow writer，依序發布：`study-created`、`preregistration-approved`、`development-authorized`、`trial-recorded`、`trial-registry-frozen`、`provenance-audited`、`candidate-frozen`。

Artifact 發布後不可覆寫。若未被事件引用的 artifact 有錯，保留原檔並用新路徑發布修正版。使用既有 authority root；不確定時先向使用者確認。中斷時先用 writer `recover`，不要手動補 event。

## 7. Freeze 前驗證

- Source Bundle 逐檔 SHA-256 相符；
- snapshot manifest 與實際 SHA-256 相符；
- YAML 為 repository-canonical；
- qualification gates 與 preregistration 完全相同；
- selection rule digest 包含 eligibility、selection 與 tie handling；
- Candidate Freeze 綁定 registry、candidate、qualification、snapshot set、fold inventory、selection evidence；
- Ruff、策略測試、workflow tests、writer validate、`git diff --check` 全部通過；
- 最後事件是 `candidate-frozen`，沒有 `000008-*`。
