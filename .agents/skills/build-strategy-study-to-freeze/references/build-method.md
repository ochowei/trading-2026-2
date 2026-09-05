# 新 Study 建立方法

## 1. 研究設計

先把上一輪觀察分成三類：已確認的規格／實作缺陷、Development 警訊、未驗證設計假說。流程缺陷可以一起修正；策略本身每輪只選一個可歸因的主要變更，除非多個條件在經濟機制上不可分割。

預先寫清楚 setup、trigger、決策與成交時間、stop、target、holding、gap、同 session 歧義、成本、position sizing、cooldown clock、Candidate Family、Trial budget、baseline、選擇規則及各階段 gates。

不要根據已看過的 Development 數值，把門檻設在剛好能通過的位置而不說明依據。沿用舊 Development 時，在 provenance 明確標示 `development-informed`。

## 2. 同名 research bundle 與資料 reference

建立 `research/<study-id>/` 放置 Study 專屬的規格、runner、evidence binding 與研究紀錄；raw
market data 預設不複製到這個目錄。資料重用採 shared reference-first，詳細欄位與判斷順序見
[`data-reuse.md`](data-reuse.md)。

優先 reference `research/market-data/<provider>/` 下已通過品質檢查、內容定址的公用快照；若
只有舊 Study 有相容檔案，先公用化一次再 reference，除非有明確理由不能公用化。workflow
的 `data-snapshot-set.yml` role entry 必須維持 `data-snapshot.schema.yml` 要求的固定欄位，
不能直接加入 `data_source`、`path` 或 `view` 等額外欄位。每個 role 的 source path、source
digest、品質報告與不重疊 session view，應記在 Study 的 acquisition/lineage manifest，並由
Development inputs 與 runner 明確綁定。
同一份完整公用快照可以被多個 role reference，但 runner 必須依明確日期範圍和 XNYS inventory
切 view，並核對 view digest；不能靠檔名或目前資料夾位置猜測來源。

Development runner 只可開啟 2013 warmup-only 與 2014--2018 Development view。若 runner 只
接受實體 CSV，才在 Study 內物化副本，並保留 source reference、source digest 和物化原因；
這是相容性 fallback，不是預設流程。

Historical Evaluation 與 quarantine 在 candidate freeze 前只保存 reference metadata，
不得讀取內容、輸出統計或執行策略。正式 run 不得連線 provider 更新公用快照。

## 3. Outcome-relevant 程式

不要修改已被其他 Study Source Bundle 凍結的檔案。新增獨立策略模組與測試，或在不影響舊 digest 的前提下重用既有模組。

Source Bundle 至少包含策略引擎、直接依賴、測試、Development runner、Historical Evaluation runner、preregistration、qualification spec、implementation contract、`pyproject.toml` 與 lockfile。對本 workflow v001 的新 Study，Implementation contract 一律放在
`research/<study-id>/implementation-contract.yml`，Source Bundle 必須綁定這個完全相同的 path 與 digest；不得再發布
`workflows/.../studies/<study-id>/manifests/implementation-contract.yml`。`studyctl contract` 會優先解析 Study manifest 的 contract，錯誤的第二份 contract 會遮蔽 research contract，並造成 `contract-not-frozen`。它至少要固定引擎規格常數、成本常數、各指標的 lookback／`min_periods`／not-ready 語意、RSI 的零 gain/loss 分支、volume lead 的 prior-only 語意，以及 stop、target、gap、同日先後順序、holding 與 cooldown 等 outcome 邊界。

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
```

執行器產生的每個 Development gate 名稱、operator 與 required value也必須逐項相同。不得靜默新增 gate。

此外，逐一把 Evaluation gate 名稱對照 `validator/artifacts.py` 實際產生的 metrics。v001 Historical Evaluation 的 drawdown metric 名稱是 `stress_max_drawdown`；不得使用看似合理但 validator 不會產生的別名，也不得在不更新並重新 release workflow validator 的情況下加入自訂正式 metric。Freeze 前應以空白合成 evidence 跑一次 validator gate-support preflight。

此外，在 writer 建立 Study 並發布必要 manifests 後，先確認 Study manifest 沒有第二份
implementation contract，且 Source Bundle 的 contract entry 精確指向同名 research path
與 digest；至少在 `preregistration-approved` 前執行 `studyctl contract` 與
`studyctl synthetic`。候選選擇與
freeze 前 artifacts 完成後，追加 `candidate-frozen` 前必須從 repository 根目錄執行：

```bash
uv run python research/tools/studyctl.py \
  --repository-root . \
  --authority-root <authority-root> \
  all <study-id>
```

CLI 必須 exit code 0 且輸出 `status: "passed"`；`--authority-root` 省略時只能作為本地
定位，不能作為正式 freeze 的完成證據。CLI 只讀取與檢查，不得取代 writer 或 validator。

## 5. Development

在 preregistration-approved 與 development-authorized 後，按 Trial budget 執行。每個曾查看結果且 outcome-relevant inputs 不同的版本都是新 Trial。

Development evidence 至少保存 base/stress 逐筆交易、pre-entry equity 比例、主要 metrics、signal-year 分段、preregistered leave-one-year-out、block bootstrap、完整 gates、network access 與全部 frozen digests。由 raw trades 重算摘要，不信任 runner 自報 disposition。

## 6. Writer 事件鏈

只使用 workflow writer，依序發布：`study-created`、`preregistration-approved`、`development-authorized`、`trial-recorded`、`trial-registry-frozen`、`provenance-audited`、`candidate-frozen`。Candidate freeze 前的 CLI 通過不會自行追加事件；必須在 CLI 通過後仍由 writer 發布最後事件。

Artifact 發布後不可覆寫。若未被事件引用的 artifact 有錯，保留原檔並用新路徑發布修正版。使用既有 authority root；不確定時先向使用者確認。中斷時先用 writer `recover`，不要手動補 event。

## 7. Freeze 前驗證

- Source Bundle 逐檔 SHA-256 相符；
- snapshot manifest 與實際 SHA-256 相符；
- YAML 為 repository-canonical；
- implementation contract 只存在於 canonical research path、已被 Source Bundle 以相同 path/digest 綁定，Study manifest 沒有第二份 contract，且 `studyctl contract` 與 `studyctl synthetic` 通過；
- qualification gates 與 preregistration 完全相同；
- selection rule digest 包含 eligibility、selection 與 tie handling；
- Candidate Freeze 綁定 registry、candidate、qualification、snapshot set、fold inventory、selection evidence；
- Ruff、策略測試、workflow tests、writer validate、`git diff --check` 全部通過；
- `studyctl all` 執行時帶 `--authority-root`，exit code 為 0、輸出 `status: "passed"`，且沒有未處理的 warning；
- 最後事件是 `candidate-frozen`，沒有 `000008-*`。

若 Development gate 失敗且 projection 已是合法的 `terminal-without-candidate`，candidate freeze
不適用，不得為了滿足上述 candidate artifact 清單而製造候選證據；此時核對 terminal state、
authority 與既有 artifact 的必要錯誤後，依提前終止規則交接。
