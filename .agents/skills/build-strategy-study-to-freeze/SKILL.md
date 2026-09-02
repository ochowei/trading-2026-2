---
name: build-strategy-study-to-freeze
description: 為 strategy-forward-replication-research--v001 建立單一新 Study，完成預先登記、Development、provenance、候選選擇與 candidate freeze，並以 Study preflight CLI 驗證規格與實作後，在執行 Historical Evaluation 前停止。使用者要求開發新策略 Study、建立下一輪研究或做到 Evaluation 前時使用；不接手既有 Study 的 Evaluation、challenge、replay 或 terminal 階段。
---

# 建立策略 Study 至候選凍結

只處理 repository 內 `strategy-forward-replication-research--v001` 的一個新 Study。目標是留下可由下一個 task 安全接手的 `candidate-frozen` 事件鏈，不是取得正式結果。

本 skill 必須搭配 repository 的唯讀 `research/tools/studyctl.py`。它補足人工閱讀與 writer validator 不容易及早發現的規格／實作落差，是 candidate freeze 前的硬閘門；它不會寫入 Event，也不取代 workflow writer 或 validator。

## 開始條件

- 使用者須指定或明確授權建立一個新 Study；可以合理命名 Study ID，但要先告知使用者。
- 在任何寫入前執行：

```bash
python3 .agents/skills/build-strategy-study-to-freeze/scripts/check_new_study.py <study-id>
```

- 只有輸出 `eligible` 且 exit code 0 才能繼續。不得覆寫、恢復或改名既有 Study 來冒充新 Study。
- `check_new_study.py` 只確認 Study ID 可以建立；Study 目錄、research bundle、Source Bundle 與 implementation contract 建好後，仍必須依下方規則執行 `studyctl`。
- 先確認目前 task 沒有看過這個候選的 Historical Evaluation、challenge 或 replay 策略結果。若已曝光，不得宣告 `verified-clean`；依 workflow 記錄實際 provenance。
- 讀取並遵守 repository `AGENTS.md`、workflow release、guide、rules、schemas、writer 與 validator。不得使用 `--allow-draft`。

## 不可跨越的邊界

- 可以使用 warmup-only 與 Development 資料開發；不得用 quarantine、Historical Evaluation 或 replay 價格調參、選模或檢查策略績效。
- 正式資料優先引用 repository 公用的 immutable snapshot；只有 runner 或正式 artifact 明確無法解析 reference 時，才可建立 Study 內的物化副本。資料重用本身不得在本 skill 執行策略。
- 不得執行或發布 `historical-evaluation-completed` 及其後事件。
- Candidate freeze 後不得修改 Source Bundle、候選、資格規格、資料綁定、選擇證據或任何 outcome-relevant 程式。
- 任一 Development gate 失敗時保留 Trial，依 preregistered 規則凍結 registry 並走提前終止；不得調低 gate 後重跑成同一 Study。

## 資料取得與 shared reference-first

資料重用時必須先閱讀 [references/data-reuse.md](references/data-reuse.md)。其中的
`reference` 是「以 repository-relative path 加上內容 digest 指向既有檔案」，不是 symlink，
也不是不帶版本的 `latest.csv`。

- 既有 ticker 先查找 `research/market-data/yahoo/` 的公用快照；只有找不到完全相容的
  公用快照時，才查找既有 Study 的內容定址快照。公用資料是預設來源，Study-local 資料是
  fallback，不得反過來優先。
- 比對 ticker、資料起訖日或可切出的 session range、provider、交易所日曆、`1d` 頻率、
  auto-adjusted 設定、欄位、品質報告與實際 SHA-256。不能因檔名相近就載入，也不能把不同
  調整方式或不同區間靜默當成相同資料。
- 找到相容的公用快照時，workflow 的 `data-snapshot-set.yml` role entry 仍須完全符合
  `data-snapshot.schema.yml`：保留 role、sessions 與 `data_digest` 等固定欄位，不要把
  `data_source`、`path` 或 `view` 等額外欄位直接塞進 role entry。shared source path、source
  digest、品質報告與每個 role 的不重疊 view，應記在 Study 的 acquisition/lineage manifest，
  並與 Development inputs、runner 綁定；不要把相同 CSV 複製到
  `research/<new-study-id>/data/snapshots/`。同一份公用完整快照可以由不同 role 以明確的日期
  範圍切 view，但每個 view 都必須重新核對 XNYS session inventory 與 view digest。
- 若只有舊 Study 有相容資料，優先把它依原 digest 不可覆寫地登錄為公用 immutable snapshot，
  新 Study 再 reference 公用路徑；只有這個公用化流程不適用時，才直接 reference 舊 Study
  路徑，並在 provenance 記錄原因。若 runner 無法解析 reference，才可在 Study 內物化副本，
  並同時保存原始 source path、source digest 與物化原因。
- 新 ticker 或既有資料覆蓋不到的新日期區間，使用 repository 共用工具
  `research/tools/download_market_data.py` 下載到 `research/market-data/yahoo/`；通過資料
  品質檢查後，後續 Study 以 reference 使用，不預設每個 Study 各自下載一份。
- 不論採 reference 或物化副本，仍須依 workflow 固定角色維持不重疊的
  `warmup-only`、`development`、`quarantine`、`historical-evaluation` 與
  `retrospective-execution-replay` views。Development 只能開啟允許的 warmup 與 Development
  view，Evaluation、quarantine 與 replay 資料在 candidate freeze 前不得用來調參、選模或
  檢查策略績效。

## 必做工作

完整閱讀 [references/build-method.md](references/build-method.md)，依其順序建立研究。特別確保：

1. 新假說只包含能清楚歸因的有限變更，並有可否證 gate。
2. Preregistration、qualification spec 與執行器對 Development、Evaluation、replay gate 完全一致，而且每個正式 gate 都是 workflow validator 能重算的 metric。
3. Source Bundle 在 Study 建立前納入所有 outcome-relevant 程式，包括 Development runner、Historical Evaluation runner、策略引擎、測試與 implementation contract；每個 contract 檔案都必須有明確路徑與 digest 綁定。
4. Historical Evaluation runner 必須能只靠 frozen inputs 產生 schema-compliant raw evidence；本 skill 只能用合成資料測試它，不得對正式 Evaluation snapshot 執行。
5. Development evidence 保存 preregistered 分段、leave-one-year-out、block bootstrap 或其他診斷，不得只保存摘要 pass/fail。
6. Study 與 `research/<study-id>/` 使用同一 ID；正式 artifacts 只經 guarded writer 發布，事件只經 writer 追加；raw data 預設以公用 shared reference 綁定，不因 Study ID 而複製一份。
7. 最後執行完整測試、Ruff、Source Bundle hash 重算與 writer validator。

## CLI 前置檢查與 implementation contract

每個新 Study 都必須有一份明確的 implementation contract。優先使用
`research/<study-id>/implementation-contract.yml`，並把它納入 Study 與 research 的
Source Bundle；若 workflow schema 要求設定直接放在 candidate-definition 或
preregistration，也可以內嵌，但必須由 candidate／preregistration manifest 綁定，不能成為
未追蹤的旁路設定。至少要說清楚：

- 策略引擎路徑、`DEFAULT_SPEC`（或等價規格常數）與成本常數；
- SMA、RSI、volume lead 的欄位、lookback、`min_periods` 與有效歷史長度；
- RSI 使用的公式、尚未 ready 時的值，以及 gain/loss 同時為零、只有 loss 為零、只有 gain 為零時的處理；
- volume lead 是否只使用前一個 session 可取得的資料；
- stop、target、gap、同日先後順序、holding span、cooldown 等會改變 outcome 的邊界語意。

執行順序如下：

1. 任何寫入前先跑 `check_new_study.py`。這一步不能用 `studyctl all` 取代，因為此時新 Study 的必要檔案尚未存在。
2. Study、同名 research bundle、preregistration、candidate、qualification、Source Bundle 與 implementation contract 已由正式 writer 發布後，至少在 `preregistration-approved` 前跑一次 `contract` 與 `synthetic`；需要定位問題時可先分開跑 `identity`。
3. 候選選擇證據與所有 freeze 前 artifact 完成後、追加 `candidate-frozen` 前，從 repository 根目錄執行：

```bash
uv run python research/tools/studyctl.py \
  --repository-root . \
  --authority-root <authority-root> \
  all <study-id>
```

`--authority-root` 是正式 freeze 流程的必要參數；若只是本地開發定位問題可以省略，但不能把未核對 authority checkpoints 的結果當成正式 freeze 通過。CLI 輸出必須是 `status: "passed"` 且 exit code 0；所有 warning 都要檢查，正式 freeze 不得留下 `authority-not-checked`。不要用 `--allow-draft`、忽略 exit code，或修改 CLI 來掩蓋失敗。

`all` 會依序檢查 identity、contract、synthetic 與 freeze。以下任一類問題都必須先修正或依 preregistered 規則終止 Study：舊 Study 路徑殘留、candidate／preregistration／qualification 不一致、validator 不支援的 gate、warmup 太短、指標尚未 ready 就被使用、RSI／交易邊界語意不明、Source Bundle 或 authority digest 不符，以及 workflow validator 拒絕。

Development gate 失敗而 workflow 已合法進入 `terminal-without-candidate` 時，candidate freeze 不適用；不要為了讓 CLI 通過而補造 candidate、selection 或 provenance evidence。此分支應核對 `studyctl freeze` 回報的 terminal state 與 authority，然後依提前終止規則交接；若 CLI 回報的是已存在 artifact 的實際錯誤，仍須修正或記錄。

`studyctl` 是檢查器，不是事件發布器。通過後仍只能用 guarded writer 追加 `candidate-frozen`，並立即重新執行 writer validator；CLI 的命令、Study ID、status、contract 路徑、derived history、Source Bundle digest 與 authority 驗證結果要記入交接摘要或既有 audit 紀錄。

## 完成與交接

成功時必須確認目前事件恰為 `candidate-frozen`、outcome 仍為 pending，並回報：

- Study ID、candidate ID 與核心假說；
- Development gates、主要結果與不確定性；
- Source Bundle digest、event-chain head 與 authority root；
- frozen Historical Evaluation runner 路徑；
- candidate freeze 前 `studyctl all` 的通過結果，以及 implementation contract 路徑與驗證摘要；
- 明確聲明沒有執行或讀取正式 Evaluation、challenge、replay 策略結果。

不要自動接續 Historical Evaluation。使用者另行要求後，交給 `$run-strategy-historical-evaluation`。
