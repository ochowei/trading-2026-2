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
