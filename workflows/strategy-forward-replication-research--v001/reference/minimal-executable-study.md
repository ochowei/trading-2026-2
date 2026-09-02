# Study 最小可執行規格

本文件將 `strategy-forward-replication-research` 的研究流程縮減為最小可執行規格。詳細規則與
解釋請參考 [`strategy-forward-replication-research-v001-guide.md`](strategy-forward-replication-research-v001-guide.md)。

## 目的

在不省略 trial、digest、provenance 與 immutable evidence 控制的前提下，以固定資料區間開發、
凍結及驗證唯一候選策略，降低 lookahead bias、selection bias、過度擬合及不實際成交假設造成的
回測失真。

本流程使用的 outcome windows 都是歷史資料，因此結果只代表回溯穩健性，不保證未來績效，也不
授予實盤交易權限。

## 固定資料區間

| 資料角色 | 日期 | 用途 |
|---|---|---|
| Warmup-only | 2013-01-01 至 2013-12-31 | 指標前置觀察，不計入績效 |
| Development | 2014-01-01 至 2018-12-31 | 開發、比較及選擇策略 |
| Quarantine | 2019-01-01 至 2019-12-31 | 隔離，不得移入其他資料角色 |
| Historical Evaluation | 2020-01-01 至 2024-12-31 | 五個互不重疊的年度 folds |
| Retrospective execution replay | 2025-01-01 至 2025-12-31 | 依時間順序進行歷史成交重播 |

不得自行更換、縮短或延長日期，不得增加、遺漏或重疊 sessions。

## 最小執行流程

### 1. 建立 study identity

為每次研究指定：

- 唯一 study ID；
- 唯一 research-round identity；
- experiment family；
- human research owner；
- replay operator；
- exact workflow 與 policy-set identity。

### 2. 預先登記並凍結規則

查看正式 Evaluation 或 replay outcome 前，預先登記並凍結：

- 可否證的研究假說；
- 完整候選集合；
- 最大 trial 數；
- 候選 eligibility、排序、選擇及同分處理規則；
- distinct family baseline；
- 交易、成交及持有規則；
- base 與 stress costs；
- 風險上限；
- robustness challenges；
- Evaluation、replay、pause、recovery 與 outcome 門檻。

上述規格不得依賴未明示的預設值。

### 3. 在 Development 開發並記錄全部 trials

策略開發只能使用 Development evidence。每個曾查看結果且可能影響選擇的 outcome-relevant 策略
版本都算一個 trial，包括失敗、移除及放棄的版本。

全部 trials 必須寫入 append-only trial registry，不得刪除、隱藏或回填不存在的歷史紀錄。達到
最大 trial 數仍沒有合格候選時，本次 study 終止。

### 4. 完成 provenance audit

查看正式 Evaluation 或 replay outcome 前，必須稽核資料、策略及既有 outcome exposure 的來源，
並將 asset-specific provenance 凍結為下列其中一種：

- `verified-clean`；
- `known-contaminated`；
- `provenance-unknown`。

缺少證明時必須使用 `provenance-unknown`。已看過的 outcome 不能因為更換研究者或建立新 study 而
重新視為 unseen evidence。

### 5. 選擇並凍結唯一候選

依預先登記的規則，從完整 trial family 選出至多一個候選，以及一個不同且較簡單的 family
baseline。

候選凍結時至少保存並綁定：

- selected candidate 與完整 trial family；
- strategy definition digest；
- market-data snapshot digest；
- workflow 與 policy-set digests；
- trial registry digest；
- qualification specification digest；
- Source Bundle digest（把會影響結果的程式與設定列成檔案清單，不要求 Git）；
- selection evidence digest（證明候選是依預先登記的排序規則選出）；
- human approval identity 與時間。

凍結後不得調參、重新排名、擴大候選集合或更換候選。

### 6. 產生 immutable evidence

Development、candidate freeze、Evaluation、challenges、replay 與 terminal review 的正式輸入和結果，
都必須保存為不可覆寫的 artifacts，並透過 exact digest 相互綁定。

Evidence 一旦被 digest 引用，就不得覆寫、刪除、改名或以 mutable `latest` pointer 取代。相同輸入
的 recovery 只能恢復或完成同一 frozen operation，不得改變策略、資料、門檻或 publication decision。

### 7. 執行 Historical Evaluation 與 robustness challenges

使用凍結候選、immutable snapshots 和 offline runs，評估 2020 至 2024 五個互不重疊的年度 folds。
每筆交易依 signal date 歸屬，並在同一 fold 內退出。

至少執行下列 challenges：

1. 現金基準；
2. 不同且較簡單的 family baseline；
3. exposure-matched 隨機進場；
4. 預先登記的小幅參數擾動；
5. 延後進場；
6. 較高成本；
7. 較差成交；
8. 漏單；
9. 市場 regime 檢查。

所有門檻都必須在 outcome 前登記。任一必要 gate 失敗，本次 study 即停止。

### 8. 執行 2025 historical replay

只有已保存且通過 Historical Evaluation 的候選才能進入 replay。Replay 必須綁定相同 study、
candidate freeze、plan、policy set、data generation 與完整 2025 session inventory，並依 session 順序
產生：

- non-actionable paper proposals；
- canonical simulated fills；
- position、cash 與 ledger events；
- base 與 stress metrics；
- checkpoint prefixes；
- historical drift assessment。

Replay 只產生歷史模擬 evidence，不得建立 broker order、真實成交或實際部位。

### 9. 重算並判定結果

Reviewer 必須從 frozen inputs、exact digests、registry 與 immutable evidence 重算所有必要結果，
不得信任執行者或 manifest 自行宣告的 `pass`，也不得在 review 時補資料、改門檻或調整策略。
Reviewer 可以和 research owner、replay operator 或 evidence producer 是同一人；這裡的「獨立」指
重新計算，不要求不同人員。

結果只能是：

- `pass`：全部必要 gates 通過，只取得 `retrospectively-supported`；
- `fail`：任一可判定的必要 gate 失敗；
- `indeterminate`：identity、資料、artifact、approval、provenance 或 integrity 不足以可信判定。

## 不可變更規則

Evaluation 或 replay 失敗後，不得：

- 更換策略或重新調參；
- 刪除、隱藏或重寫 trial；
- 更換、增加或延長資料期間；
- 改用不同的 data generation；
- 降低成本、風險或績效門檻；
- 覆寫 evidence；
- 將相同歷史 evidence 宣稱為新的 clean 或 prospective evidence。

## 最短執行摘要

> 預先凍結 study 規則；只用 Development 資料開發並以 append-only 方式記錄所有 trials；完成
> provenance audit 後，以 exact digests 凍結唯一候選及全部輸入；再依序執行 Historical
> Evaluation、robustness challenges 和 historical replay，將各階段結果保存為 immutable evidence；
> 最後由 independent reviewer 重算。任何失敗都不得修改策略、資料或門檻後重試。
