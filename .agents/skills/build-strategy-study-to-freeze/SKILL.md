---
name: build-strategy-study-to-freeze
description: 為 strategy-forward-replication-research--v001 建立單一新 Study，完成預先登記、Development、provenance、候選選擇與 candidate freeze，並在執行 Historical Evaluation 前停止。使用者要求開發新策略 Study、建立下一輪研究或做到 Evaluation 前時使用；不接手既有 Study 的 Evaluation、challenge、replay 或 terminal 階段。
---

# 建立策略 Study 至候選凍結

只處理 repository 內 `strategy-forward-replication-research--v001` 的一個新 Study。目標是留下可由下一個 task 安全接手的 `candidate-frozen` 事件鏈，不是取得正式結果。

## 開始條件

- 使用者須指定或明確授權建立一個新 Study；可以合理命名 Study ID，但要先告知使用者。
- 在任何寫入前執行：

```bash
python3 .agents/skills/build-strategy-study-to-freeze/scripts/check_new_study.py <study-id>
```

- 只有輸出 `eligible` 且 exit code 0 才能繼續。不得覆寫、恢復或改名既有 Study 來冒充新 Study。
- 先確認目前 task 沒有看過這個候選的 Historical Evaluation、challenge 或 replay 策略結果。若已曝光，不得宣告 `verified-clean`；依 workflow 記錄實際 provenance。
- 讀取並遵守 repository `AGENTS.md`、workflow release、guide、rules、schemas、writer 與 validator。不得使用 `--allow-draft`。

## 不可跨越的邊界

- 可以使用 warmup-only 與 Development 資料開發；不得用 quarantine、Historical Evaluation 或 replay 價格調參、選模或檢查策略績效。
- 正式資料可依既有 immutable digest 機械複製、建立同名路徑與核對 hash，但不得在本 skill 執行策略。
- 不得執行或發布 `historical-evaluation-completed` 及其後事件。
- Candidate freeze 後不得修改 Source Bundle、候選、資格規格、資料綁定、選擇證據或任何 outcome-relevant 程式。
- 任一 Development gate 失敗時保留 Trial，依 preregistered 規則凍結 registry 並走提前終止；不得調低 gate 後重跑成同一 Study。

## 資料取得與既有快照重用

- 新 ticker 或既有資料覆蓋不到的新日期區間，使用 repository 共用工具
  `research/tools/download_market_data.py` 下載 Yahoo Finance 的 1d、auto-adjusted
  OHLCV 資料。`--start` 與 `--end` 都是含頭含尾日期；工具會先檢查交易日清單、缺值、有限數值、正價格、非負成交量，以及
  `Low <= Open/Close <= High` 和 `Low <= High`，通過後才保存內容帶 SHA-256 的快照與
  `.quality.yml` 報告。正式 workflow 仍以 XNYS 為交易所日曆。
- 既有 ticker 應先查找 `research/market-data/yahoo/` 的共用快照，以及既有
  `research/<study-id>/data/snapshots/` 的內容定址快照。只有在 ticker、資料起訖日、
  provider、交易所日曆、`1d` 頻率、auto-adjusted 設定、欄位與品質檢查結果都相符時，才可
  依 immutable digest 機械重用；不得因檔名相近就直接載入，也不得把不同區間或不同調整
  方式的資料當成相同資料。
- 重用既有快照時，必須核對實際檔案 SHA-256，並在新 Study 的同名
  `research/<new-study-id>/` 目錄建立或機械複製所需檔案，讓新 Study 的 data binding 指向
  自己的目錄。若日期或其他設定不吻合，就用工具下載符合設定的新快照，或明確記錄資料
  無法重用；不能靜默混接兩份不同快照。
- 共用完整快照只是一份可追溯的資料來源；仍須依 workflow 的固定角色切出不重疊的
  `warmup-only`、`development`、`quarantine`、`historical-evaluation` 與
  `retrospective-execution-replay` snapshots。Development 只能開啟允許的 warmup 與
  Development 資料，Evaluation、quarantine 與 replay 資料在 candidate freeze 前不得用來
  調參、選模或檢查策略績效。

## 必做工作

完整閱讀 [references/build-method.md](references/build-method.md)，依其順序建立研究。特別確保：

1. 新假說只包含能清楚歸因的有限變更，並有可否證 gate。
2. Preregistration、qualification spec 與執行器對 Development、Evaluation、replay gate 完全一致，而且每個正式 gate 都是 workflow validator 能重算的 metric。
3. Source Bundle 在 Study 建立前納入所有 outcome-relevant 程式，包括 Development runner、Historical Evaluation runner、策略引擎與測試。
4. Historical Evaluation runner 必須能只靠 frozen inputs 產生 schema-compliant raw evidence；本 skill 只能用合成資料測試它，不得對正式 Evaluation snapshot 執行。
5. Development evidence 保存 preregistered 分段、leave-one-year-out、block bootstrap 或其他診斷，不得只保存摘要 pass/fail。
6. Study 與 `research/<study-id>/` 使用同一 ID；正式 artifacts 只經 guarded writer 發布，事件只經 writer 追加。
7. 最後執行完整測試、Ruff、Source Bundle hash 重算與 writer validator。

## 完成與交接

成功時必須確認目前事件恰為 `candidate-frozen`、outcome 仍為 pending，並回報：

- Study ID、candidate ID 與核心假說；
- Development gates、主要結果與不確定性；
- Source Bundle digest、event-chain head 與 authority root；
- frozen Historical Evaluation runner 路徑；
- 明確聲明沒有執行或讀取正式 Evaluation、challenge、replay 策略結果。

不要自動接續 Historical Evaluation。使用者另行要求後，交給 `$run-strategy-historical-evaluation`。
