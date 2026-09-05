---
name: build-strategy-study-to-freeze
description: 為 strategy-forward-replication-research--v001 建立單一新 Study，完成預先登記、Development、provenance、候選選擇與 candidate freeze，並以 Study preflight CLI 驗證規格與實作後，在執行 Historical Evaluation 前停止。使用者要求開發新策略 Study、建立下一輪研究或做到 Evaluation 前時使用；不接手既有 Study 的 Evaluation、challenge、replay 或 terminal 階段。
---

# 建立策略 Study 至候選凍結

只處理 repository 內 `strategy-forward-replication-research--v001` 的一個新 Study。目標是留下可由下一個 task 安全接手的 `candidate-frozen` 事件鏈，不是取得正式結果。

本 skill 必須搭配 repository 的唯讀 `research/tools/studyctl.py`。它補足人工閱讀與 writer validator 不容易及早發現的規格／實作落差，是 candidate freeze 前的硬閘門；它不會寫入 Event，也不取代 workflow writer 或 validator。

## 使用角色限制

- 本 skill 只能由 **study 開發者** 使用。
- 執行任何 preflight、建立 research bundle、寫入 Study 或發布 `candidate-frozen` 前，必須確認目前對話角色就是 **study 開發者**。
- 其他角色不得以本 skill 建立、修改或凍結 Study；若目前角色不符，立即停止並說明角色限制。

## 開始條件

- 使用者須指定或明確授權建立一個新 Study；可以合理命名 Study ID，但要先告知使用者。
- 在任何寫入前，先從 Git 取得目前 repository root 的絕對路徑，並固定設定
  `authority_root = <repository-root>/.authority/`。不得由 Study 目錄、既有 journal 或
  Agent 自行猜測另一個路徑；必須讓下方的 authority preflight 輸出並確認這個絕對路徑。
- 確認 authority root 後，再在任何寫入前執行：

```bash
python3 .agents/skills/build-strategy-study-to-freeze/scripts/check_new_study.py <study-id>
```

- 只有輸出 `eligible` 且 exit code 0 才能繼續。不得覆寫、恢復或改名既有 Study 來冒充新 Study。
- `check_new_study.py` 只確認 Study ID 可以建立；Study 目錄、research bundle、Source Bundle 與 implementation contract 建好後，仍必須依下方規則執行 `studyctl`。
- 先確認目前 task 沒有看過這個候選的 Historical Evaluation 或 Terminal 結果。若已曝光，不得宣告 `verified-clean`；依 workflow 記錄實際 provenance。
- 讀取並遵守 repository `AGENTS.md`、workflow release、guide、rules、schemas、writer 與 validator。不得使用 `--allow-draft`。

## Authority root 固定規則

- 新 Study 一律使用 repository-local 的 `<repository-root>/.authority/` 作為 authority root。它位於 Workflow Package 與 `workflows/.../studies/<study-id>/`、`research/<study-id>/` 之外，但刻意納入 Git；不得使用 `.study-authority/`、`/tmp`、外部路徑或其他臨時目錄。
- 在任何 writer 操作前，先把 authority root 解析成絕對路徑，確認它就是目前 repository 的 `.authority/`，並執行唯讀的 `check_authority_root.py`。不得猜測、臨時建立、搬移、清空或改用另一個 authority root。
- 新 Study 的 `<authority-root>/<study-id>/` 必須不存在或是空目錄；若已有任何 checkpoint 或其他檔案，必須停止並查明來源。
- 從 `create` 到 `append`、`recover`、`validate` 及 `studyctl all`，每次都必須傳入同一個已確認的絕對路徑。執行中不得以相對路徑或另一個看似相同的目錄代替。
- authority mismatch、checkpoint 數量不一致或 digest 不一致時，立即停止；不得刪除 checkpoint、重新 `create`、手動補 checkpoint，或換 root 重試。若有 prepared journal，只能用原本的 authority root 執行 `recover`。
- `.authority/` 不得列入 `.gitignore`。每次 Event 發布後檢查 authority 檔案的 Git 狀態，candidate freeze 交接時記錄 authority root 絕對路徑、checkpoint 數量、最後 checkpoint digest，以及 authority 檔案是否已納入 Git。
- 這套 repository-local 規則只適用新 Study；不得把既有 Study 的外部 authority checkpoint 自動搬入 `.authority/` 來冒充同一條 authority chain。

## 不可跨越的邊界

- 可以使用 warmup-only 與 Development 資料開發；不得用 quarantine 或 Historical Evaluation 價格調參、選模或檢查策略績效。
- 正式資料優先引用 repository 公用的 immutable snapshot；只有 runner 或正式 artifact 明確無法解析 reference 時，才可建立 Study 內的物化副本。資料重用本身不得在本 skill 執行策略。
- 不得執行或發布 `historical-evaluation-completed` 及其後事件。
- Candidate freeze 後不得修改 Source Bundle、候選、資格規格、資料綁定、選擇證據或任何 outcome-relevant 程式。
- 任一 Development gate 失敗時保留 Trial，依 preregistered 規則凍結 registry 並走提前終止；不得調低 gate 後重跑成同一 Study。
- `study-created` 之後若發現 implementation contract、Source Bundle 或其他 frozen binding 的完整性錯誤，且尚未產生 outcome-bearing trial，必須走 `evidence-unavailable` → `study-terminal` 的提前終止鏈；不得只在對話中宣告「停止」。

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
  `warmup-only`、`development`、`quarantine` 與 `historical-evaluation` views。Development
  只能開啟允許的 warmup 與 Development view，Evaluation 與 quarantine 資料在 candidate
  freeze 前不得用來調參、選模或檢查策略績效。

## 必做工作

完整閱讀 [references/build-method.md](references/build-method.md)，依其順序建立研究。特別確保：

1. 新假說只包含能清楚歸因的有限變更，並有可否證 gate。
2. Preregistration、qualification spec 與執行器對 Development、Evaluation gate 完全一致，而且每個正式 gate 都是 workflow validator 能重算的 metric。
3. Source Bundle 在 Study 建立前納入所有 outcome-relevant 程式，包括 Development runner、Historical Evaluation runner、策略引擎、測試與 implementation contract；每個 contract 檔案都必須有明確路徑與 digest 綁定。
4. Historical Evaluation runner 必須能只靠 frozen inputs 產生 schema-compliant raw evidence；本 skill 只能用合成資料測試它，不得對正式 Evaluation snapshot 執行。
5. Development evidence 保存 preregistered 分段、leave-one-year-out、block bootstrap 或其他診斷，不得只保存摘要 pass/fail。
6. Study 與 `research/<study-id>/` 使用同一 ID；正式 artifacts 只經 guarded writer 發布，事件只經 writer 追加；raw data 預設以公用 shared reference 綁定，不因 Study ID 而複製一份。
7. 最後執行完整測試、Ruff、Source Bundle hash 重算與 writer validator。

## CLI 前置檢查與 implementation contract

### Authority root preflight

`check_new_study.py` 只檢查 Study ID 與 Study／research 路徑唯一性，不檢查 authority root。任何新 Study 在第一次 writer 操作前都必須先執行：

```bash
uv run python .agents/skills/build-strategy-study-to-freeze/scripts/check_authority_root.py \
  <study-id> \
  --repository-root <repository-root-absolute-path> \
  --authority-root <repository-root-absolute-path>/.authority \
  --phase new
```

這個 CLI 是唯讀檢查，會確認 authority root 位於 repository 內且不在 Study 目錄，`.authority/` 沒有被 Git 忽略，並確認新 Study 的 authority 子目錄不存在或為空。只有輸出 `status: "passed"` 且 exit code 為 0，才可繼續 `check_new_study.py`、建立 research bundle 與執行 `studyctl precreate`。

Study 建立後，在 `append`、`recover`、`validate` 或正式 `studyctl all` 前，以同一個已記錄的絕對路徑改跑 `--phase existing`；它必須確認 Event chain 與 authority checkpoint chain 相符。任何失敗都要停下來，不得改用其他 root。

每個新 Study 都必須有一份明確的 implementation contract。對本 workflow
`strategy-forward-replication-research--v001` 的新 Study，一律使用
`research/<study-id>/implementation-contract.yml` 作為唯一 contract source，並把這個
**完全相同的 repository-relative path 與 digest** 納入 Source Bundle。不得另外發布
`workflows/.../studies/<study-id>/manifests/implementation-contract.yml`；Study manifest
不得存在第二份 contract。`studyctl contract` 會優先解析 Study manifest 的 contract，若它
存在但 Source Bundle 綁定的是 research path，就會產生 `contract-not-frozen`，而 immutable
artifact 不能事後以覆寫方式修正。若未來 workflow schema 要求設定直接放在
candidate-definition 或 preregistration，仍須由該 manifest 綁定同一份 contract，不能產生
第二個未同步的 contract source。至少要說清楚：

- 策略引擎路徑、`DEFAULT_SPEC`（或等價規格常數）與成本常數；
- SMA、RSI、volume lead 的欄位、lookback、`min_periods` 與有效歷史長度；
- RSI 使用的公式、尚未 ready 時的值，以及 gain/loss 同時為零、只有 loss 為零、只有 gain 為零時的處理；
- volume lead 是否只使用前一個 session 可取得的資料；
- stop、target、gap、同日先後順序、holding span、cooldown 等會改變 outcome 的邊界語意。

建立新 Study 的硬性順序是：

```text
確認 repository/.authority、執行 authority preflight 與 check_new_study
→ 建立 research bundle
→ 執行 pre-create binding preflight
→ 所有 binding 通過
→ 才能追加 study-created Event
```

`check_new_study.py` 仍只負責 Study ID 的唯一性與安全性；它不能取代
`studyctl precreate`。Research 文件建立完成後，必須先執行：

```bash
uv run python research/tools/studyctl.py \
  --repository-root . \
  precreate <study-id>
```

`precreate` 不需要任何 Study Event，會以同名 research bundle 核對跨文件 binding、
Source Bundle 檔案與 digest，以及已存在的同名 Study manifest copy。只有它輸出
`status: "passed"` 且 exit code 為 0，才可以用 guarded writer 追加第一個
`study-created` Event。Pre-create 失敗時不得建立任何 Study Event，也不得用補造
candidate、selection 或 provenance evidence 的方式讓 CLI 通過。

`study-created` 後、任何 `preregistration-approved` 或其他後續 Event 前，必須再做一次
post-create contract guard：確認 Study 內不存在
`manifests/implementation-contract.yml`，Source Bundle 的 implementation-contract entry
仍精確指向 `research/<study-id>/implementation-contract.yml`，再執行
`studyctl contract` 與 `studyctl synthetic`。如果出現 `contract-not-frozen`、path mismatch
或 digest mismatch，立即停止這個 Study；不得刪除、覆寫或重新發布既有 immutable artifact，
也不得進入 Development。因為 `study-created` 已經存在，必須依「提前終止與封存」規則追加
`evidence-unavailable`，再追加 `study-terminal`（`outcome: indeterminate`、
`authority: none`），完成原 Study 的可稽核封存後，才改用新的 Study ID。

若 preregistration 有任何改變，必須重新計算並更新所有下游 digest，包括
qualification、Development trial inputs、Source Bundle 及其所綁定的 evidence/input；
不得只修改其中一個 digest。已發布的 artifact 與 Event 一律不可覆寫；有錯時保留舊檔，
以新路徑發布修正版並由 writer 重新綁定。

Development gate 失敗時仍須保留 Trial，依 preregistered 規則進入合法的
`terminal-without-candidate`；candidate freeze 不適用，也不得為了滿足 CLI 所需欄位
製造 candidate、selection 或 provenance evidence。

### 提前終止與封存

若 `study-created` 後發生不可修復的 setup、contract、Source Bundle 或 evidence integrity
錯誤，且尚未產生可判讀策略結果，正式紀錄必須是：

1. 用 guarded writer 追加 `evidence-unavailable`，payload 至少包含
   `stage: development`、具體 `reason` 與一個目前不存在的 `unavailable_path`；不要為了
   滿足 path 欄位而建立假的 evidence artifact。
2. 以 `evidence-unavailable` event 的新 chain head 與 payload digest 建立并發布
   `evidence/terminal-evidence.yml`，其中 `outcome` 為 `indeterminate`、`authority` 為
   `none`、`recomputed` 為 `true`，並綁定目前已存在的 workflow、policy、Source Bundle
   以及（若已存在）preregistration、trial registry 與其他 evidence digest。
3. 用 guarded writer 追加 `study-terminal`，payload 使用
   `outcome: indeterminate`、`authority: none`，並綁定 terminal evidence 的 path/digest。
4. 追加每個 Event、發布 terminal evidence、`validate` 與終止狀態檢查前，都使用同一個
   `check_authority_root.py --phase existing` 與同一個絕對 authority root。終止後不得再追加
   Development、candidate freeze 或 Historical Evaluation 事件。

這種尚未產生 outcome-bearing trial 的 setup failure 應標記為 `indeterminate`，不是把沒有
績效結果的 Study 誤標成 `fail`。`study-paused` 只保留給可恢復的 technical/publication
interruption，不取代正式終止。

執行順序如下：

1. 先以 `git rev-parse --show-toplevel` 取得並記錄 repository root 絕對路徑，確認 authority root 為其 `.authority/`，執行 `check_authority_root.py --phase new`；再跑 `check_new_study.py`。這兩步都不能寫入 Study，也不能用 `studyctl all` 取代。
2. 建立 research bundle 後先跑 `studyctl precreate`；只有 binding 全部通過，才能建立 Study 目錄或追加 `study-created` Event。writer 的 `--authority-root` 必須使用同一個已確認的絕對路徑。
3. Study、同名 research bundle、preregistration、candidate、qualification、Source Bundle 與 implementation contract 已由正式 writer 發布後，先確認沒有 Study-level `manifests/implementation-contract.yml`，且 Source Bundle 綁定的是 research contract 的相同 path/digest；至少在 `preregistration-approved` 前跑一次 `contract` 與 `synthetic`。需要定位問題時可先分開跑 `identity`。Historical Evaluation runner 只能用合成資料測試，不能讀取正式 Evaluation snapshot。
4. 每次 writer 的 `append`、`recover` 或 `validate` 前都用同一個絕對路徑執行 `check_authority_root.py --phase existing`，確認仍使用同一個 authority root；若要恢復，先檢查 prepared journal 的原操作，不得用新 root 重建。
5. 候選選擇證據與所有 freeze 前 artifact 完成後、追加 `candidate-frozen` 前，從 repository 根目錄執行：

```bash
uv run python research/tools/studyctl.py \
  --repository-root . \
  --authority-root <repository-root-absolute-path>/.authority \
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
- authority root 的絕對路徑、checkpoint 數量、最後 checkpoint digest，以及 `.authority/<study-id>/checkpoints/` 的 Git 狀態；
- frozen Historical Evaluation runner 路徑；
- candidate freeze 前 `studyctl all` 的通過結果，以及 implementation contract 路徑與驗證摘要；
- 明確聲明沒有執行或讀取正式 Historical Evaluation 結果。

不要自動接續 Historical Evaluation。使用者另行要求後，交給 `$run-strategy-historical-evaluation`。

若 Study 依提前終止規則封存，交接時改為確認目前事件是 `study-terminal`、outcome 是
`indeterminate`、terminal evidence 已發布且 authority chain 通過；回報終止原因、
`evidence-unavailable` 與 `study-terminal` 的 event head、terminal evidence path/digest，
並明確說明沒有產生 Development outcome、candidate 或正式 Historical Evaluation 結果。
