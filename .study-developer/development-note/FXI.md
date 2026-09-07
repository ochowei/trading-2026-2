# FXI：Study Development 成果卡

本檔只整理 FXI 各 Study 的 Development 階段；未包含正式 Historical Evaluation、Terminal 或交易結果。

---

# `fxi-deep-pullback-no-closepos-cd7-v001`：Study Development 成果卡

- Development 判定：`通過`
- Provenance（來源可信狀態）：`verified-clean`
- 前一個 Study：無（本系列第一份；規格中的比較基準為 `fxi-single-condition-pullback-v001`）
- 記錄日期：`2026-09-08`

## 結論

> 在 2014–2018、2013 warmup、base 每邊 1 bps 費用／5 bps 滑價，以及 stress 每邊 2 bps 費用／20 bps 滑價下，本 Study 的 Development 結果支持原始假說：移除 ClosePos 條件並採用訊號後七個 session 的 cooldown，仍能通過預先登記的正報酬、獲利因子、交易數與回撤門檻。

## 研究變更

- 研究問題或假說：FXI 出現 5%–12% 深度回檔、Williams %R 超賣與短期波動高於長期波動時，不使用 ClosePos filter，並讓每次符合訊號的事件啟動七個 session 冷卻。
- 相較上一個 Study 只改：本系列首份 Study；主要策略設定是移除 ClosePos filter，並採用訊號事件驅動的七-session cooldown。
- 保持不變或比較基準：下一個 session open 進場、20 個 session 持有、-5% stop、+5.5% target 與兩套成本模型固定。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 29 | 42.64% | 1.690 | 14.01% | 通過 |
| Development / stress | 29 | 30.00% | 1.478 | 14.56% | 通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：無；完成交易 29≥20、交易年度 5≥3、base/stress 報酬均大於 0、PF 與 stress 回撤門檻均通過。
- 未執行項目與原因：無

## 主要發現

- 已確認：Development evidence 顯示兩套成本下都是 29 筆完成交易，且所有事前 gate 通過；每個 signal year 都有交易，但 2017 年只有 1 筆。
- 可能原因：較嚴格的超賣與波動條件，加上訊號後冷卻，可能降低重複進場；這只是合理解釋，現有 evidence 沒有把各條件拆開做可歸因的消融。
- 尚不能判斷：目前只能確認 Development 期間的可行性，無法由本 Study 判斷更長期間、其他市場狀態或正式結果中的可重現性；交易分布也仍偏稀疏。

## 下一輪

- 建議處置：建立有限 follow-up Study，檢查 cooldown 計時起點是否應改為完成退場後，其他規則全部固定。
- 下一個 Study 只測：將 cooldown anchor 從「接受訊號」改為「完成部位退場後」；不改訊號、成本、持有期與停損停利。
- 成功／失敗條件：完成交易至少 20 筆、交易年度至少 3 年，base/stress 報酬均大於 0、PF 分別高於 1.10／1.00，且 stress 最大回撤不超過 20%；任一失敗即否證。
- 不得沿用的問題：不得把本次通過解讀成 ClosePos、cooldown 或其他單一條件已被證明是必要原因。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-no-closepos-cd7-v001/manifests/preregistration.yml`
- Candidate definition：`workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-no-closepos-cd7-v001/manifests/candidate-definition.yml`
- Development evidence：`research/fxi-deep-pullback-no-closepos-cd7-v001/development-evidence.yml`
- 程式／測試：`src/trading_2026_2/fxi_mean_reversion.py`、`tests/test_fxi_mean_reversion.py`
- 詳細盲檢討：無

---

# `fxi-deep-pullback-no-closepos-exitcd7-v001`：Study Development 成果卡

- Development 判定：`通過`
- Provenance（來源可信狀態）：`verified-clean`
- 前一個 Study：`fxi-deep-pullback-no-closepos-cd7-v001`
- 記錄日期：`2026-09-08`

## 結論

> 在同一段 2014–2018 Development 資料與相同 base／stress 成本下，本 Study 的 Development 結果支持原始假說：把七-session cooldown 改為每次完成退場後才開始計時，仍保留正報酬與正獲利因子，並通過原定 Development gates。

## 研究變更

- 研究問題或假說：FXI 的深度回檔、超賣與波動條件維持不變，改以完成部位退場為 cooldown 起點，避免持倉期間的訊號影響下一次進場時鐘。
- 相較上一個 Study 只改：cooldown 的計時起點由接受訊號改成完成部位退場後七個完整 session。
- 保持不變或比較基準：訊號條件、下一 open 進場、20 個 session 持有、-5% stop、+5.5% target 與成本模型固定。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 22 | 26.75% | 1.527 | 12.77% | 通過 |
| Development / stress | 22 | 18.14% | 1.349 | 13.86% | 通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：無；22≥20、5≥3、兩套成本報酬與 PF 為正且 stress 最大回撤 13.86%≤20%。
- 未執行項目與原因：無；block bootstrap 與年度分解有產出，但規格標示為描述性診斷，不是額外 gate。

## 主要發現

- 已確認：Development evidence 的 22 筆交易覆蓋 5 個 signal year，base/stress 都通過正式 gate；stress block bootstrap 的正報酬比例為 81.42%／84.31%，但未被用作正式判定。
- 可能原因：以退場為時鐘可能減少持倉期間訊號造成的交易群聚；這個機制解釋尚未由獨立消融證明。
- 尚不能判斷：描述性重抽樣仍可出現超過 20% 的回撤路徑，且本 Study 沒有把 cooldown anchor 與其他條件拆成正式比較臂；因此只能確認 gate 通過，不能宣稱風險來源已被隔離。

## 下一輪

- 建議處置：建立有限 follow-up Study，加入固定的 2% 進場前資金風險預算，專門檢查單筆損失與整體回撤。
- 下一個 Study 只測：只改部位大小，使含成本的固定 stop 風險上限為進場前資金 2%；訊號、退場後 cooldown、成本與持有期不變。
- 成功／失敗條件：除原有 gate 外，單筆實現虧損不超過 4%，stress 最大回撤不超過 10%，stress block bootstrap 正報酬比例至少 80%，且 leave-one-signal-year-out 的 stress 報酬與 PF 仍分別大於 0 與 1。
- 不得沿用的問題：不得把描述性 bootstrap 的比例當成已通過的正式穩健性證明。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-no-closepos-exitcd7-v001/manifests/preregistration.yml`
- Candidate definition：`workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-no-closepos-exitcd7-v001/manifests/candidate-definition.yml`
- Development evidence：`research/fxi-deep-pullback-no-closepos-exitcd7-v001/development.yml`
- 程式／測試：`src/trading_2026_2/fxi_mean_reversion_exit_cooldown.py`、`tests/test_fxi_mean_reversion_exit_cooldown.py`、`research/fxi-deep-pullback-no-closepos-exitcd7-v001/run_development.py`
- 詳細盲檢討：無

---

# `fxi-deep-pullback-risk2-exitcd7-v001`：Study Development 成果卡

- Development 判定：`通過`
- Provenance（來源可信狀態）：`verified-clean`
- 前一個 Study：`fxi-deep-pullback-no-closepos-exitcd7-v001`
- 記錄日期：`2026-09-08`

## 結論

> 在 2014–2018 Development 與相同成本下，本 Study 的 Development 結果支持原始假說：將每筆交易的含成本 stop 風險限制為進場前資金 2%，可在 22 筆交易上維持正報酬與 PF，並把 stress 最大回撤壓在 10% 內；額外的抽樣與逐年剔除 gates 也全部通過。

## 研究變更

- 研究問題或假說：維持 FXI 深度回檔、超賣、ATR ratio 與退場後七-session cooldown，只改用可用現金與 2% stop risk budget 共同決定股數。
- 相較上一個 Study 只改：部位大小加入進場前資金 2% 的風險預算；策略訊號與退場規則不變。
- 保持不變或比較基準：base 每邊 1／5 bps、stress 每邊 2／20 bps，-5% stop、+5.5% target、20-session 持有與下一 open 進場固定。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 22 | 10.52% | 1.589 | 5.12% | 通過 |
| Development / stress | 22 | 7.10% | 1.404 | 5.21% | 通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：無；最大單筆實現虧損 base 3.42%、stress 3.33% 均≤4%，stress bootstrap 正報酬比例最低 83.76%≥80%，leave-one-year-out 的 stress 報酬、PF、回撤也全數通過。
- 未執行項目與原因：無

## 主要發現

- 已確認：Development evidence 顯示 22 筆交易、5 個年度，所有正式 gates 通過；stress 的最大單筆實現虧損為 3.33%，逐年剔除後最低 stress 報酬仍為 3.47%。
- 可能原因：固定風險部位大小直接限制了單筆損失與累積回撤；這支持風險預算的程序效果，但不能單獨證明訊號本身更有預測力。
- 尚不能判斷：樣本仍只有 22 筆，且每個年度交易數不均；重抽樣與 leave-one-year-out 是 Development 內的穩健性檢查，不能回答未來資料是否同樣成立。

## 下一輪

- 建議處置：建立程序 follow-up，先確認 workflow 能從 raw trades 重算全部 metrics、年度分段、leave-one-year-out、bootstrap 與 gates。
- 下一個 Study 只測：不改策略，只改 evidence 產生與重算流程，要求輸出欄位逐一等於 raw trades 的重算值。
- 成功／失敗條件：所有 metrics、年度分段、重抽樣、leave-one-year-out 與 gates 與獨立重算一致，且原有 gates 全數通過；任一欄位不一致即失敗。
- 不得沿用的問題：不得在程序驗證 Study 中調整訊號、成本、seed 或風險預算來修飾結果。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-risk2-exitcd7-v001/manifests/preregistration.yml`
- Candidate definition：`workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-risk2-exitcd7-v001/manifests/candidate-definition.yml`
- Development evidence：`research/fxi-deep-pullback-risk2-exitcd7-v001/development.yml`
- 程式／測試：`src/trading_2026_2/fxi_mean_reversion_risk_budget.py`、`tests/test_fxi_mean_reversion_risk_budget.py`、`research/fxi-deep-pullback-risk2-exitcd7-v001/run_development.py`
- 詳細盲檢討：無

---

# `fxi-deep-pullback-risk2-exitcd7-devverify-v001`：Study Development 成果卡

- Development 判定：`通過`
- Provenance（來源可信狀態）：`verified-clean`
- 前一個 Study：`fxi-deep-pullback-risk2-exitcd7-v001`
- 記錄日期：`2026-09-08`

## 結論

> 在策略、資料、成本、風險預算、seed 與退場規則完全不變的前提下，本 Study 的 Development 結果支持「workflow 能正確重算並核對 evidence」這個程序假說：22 筆交易的 base/stress metrics、年度分段、leave-one-year-out、block bootstrap 與所有 gates 均能由 Development raw trades 支持並通過。

## 研究變更

- 研究問題或假說：不是重新測策略，而是確認 Development raw trades 能否重建所有摘要欄位與完整 gate。
- 相較上一個 Study 只改：只改 workflow 的 evidence 重算與一致性驗證；不改策略與交易規則。
- 保持不變或比較基準：FXI 訊號、2% risk budget、退場後七-session cooldown、20-session 持有、成本、seed 與資料期間固定。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 22 | 10.52% | 1.589 | 5.12% | 通過 |
| Development / stress | 22 | 7.10% | 1.404 | 5.21% | 通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：無；完整 Development gates 與 evidence 重算核對均通過。
- 未執行項目與原因：無；block bootstrap（50,000 次、長度 3／5）與 leave-one-year-out 均有輸出。

## 主要發現

- 已確認：evidence 標示 stage 為 Development、network access 為 false，22 筆交易的 metrics 與所有 gate 都有明確值；stress bootstrap 正報酬比例為 83.76%／86.81%，逐年剔除後最低 PF 為 1.242。
- 可能原因：結果穩定是因 raw-trade 計算與摘要產出一致，而非策略在本輪被重新優化；這是程序一致性的證據。
- 尚不能判斷：本 Study 不能增加策略經濟有效性的證據強度，也不能回答 seed 以外的資料或執行變更是否會影響結果；另仍需把 seed 綁定本身單獨驗證。

## 下一輪

- 建議處置：建立有限程序 follow-up，修正並固定 bootstrap seed 的直接綁定。
- 下一個 Study 只測：每個 block length 都直接使用 preregistered seed `20260904`；不改 raw trades、策略、成本或其他 diagnostics。
- 成功／失敗條件：seed 使用位置與 evidence bindings 一致，所有重算欄位與 gates 全數通過；任何 seed 漂移或欄位不一致即失敗。
- 不得沿用的問題：不得因 seed 改變而重新選擇策略參數，或把程序修正當成策略改良。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-risk2-exitcd7-devverify-v001/manifests/preregistration.yml`
- Candidate definition：`workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-risk2-exitcd7-devverify-v001/manifests/candidate-definition.yml`
- Development evidence：`research/fxi-deep-pullback-risk2-exitcd7-devverify-v001/development.yml`
- 程式／測試：`src/trading_2026_2/fxi_risk2_seedfix.py`、`tests/test_fxi_risk2_seedfix.py`、`research/fxi-deep-pullback-risk2-exitcd7-devverify-v001/run_development.py`
- 詳細盲檢討：無

---

# `fxi-deep-pullback-risk2-exitcd7-seedfix-v001`：Study Development 成果卡

- Development 判定：`通過`
- Provenance（來源可信狀態）：`verified-clean`
- 前一個 Study：`fxi-deep-pullback-risk2-exitcd7-devverify-v001`
- 記錄日期：`2026-09-08`

## 結論

> 在完全不改 FXI 策略、資料、成本、風險預算與退場規則下，本 Study 的 Development 結果支持「bootstrap seed 依預先登記值直接綁定」的程序假說：22 筆交易的 base/stress 結果與額外穩健性 gates 全部通過，且每個 block length 都使用 seed `20260904`。

## 研究變更

- 研究問題或假說：確認 Development block bootstrap 不會因 block length 而偷偷換用另一個 seed，並維持原有完整 gates。
- 相較上一個 Study 只改：只改 bootstrap seed 的直接套用與 evidence 綁定；沒有策略變更。
- 保持不變或比較基準：FXI 訊號、2% risk budget、退場後七-session cooldown、成本、20-session 持有、stop／target 與資料期間固定。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 22 | 10.52% | 1.589 | 5.12% | 通過 |
| Development / stress | 22 | 7.10% | 1.404 | 5.21% | 通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：無；完成交易、報酬、PF、回撤、單筆損失、bootstrap 與 leave-one-year-out gates 均通過。
- 未執行項目與原因：無

## 主要發現

- 已確認：Development evidence 的 base/stress metrics 與 risk2 Study 規格一致，stress block bootstrap 正報酬比例為 83.76%／86.81%，最大 stress 單筆實現虧損為 3.33%。
- 可能原因：固定 seed 讓不同 block length 的抽樣結果可重現、可核對；這提升的是 evidence 的可追溯性，不是報酬本身。
- 尚不能判斷：即使程序與 gates 通過，樣本仍只有 22 筆、跨 5 年且年度交易不均；本卡不能把程序潔淨度延伸成未來績效保證。

## 下一輪

- 建議處置：停止新增策略 Study，保留本版作 candidate freeze preflight 的 Development 依據。
- 下一個 Study 只測：不建議再改策略；若 workflow 仍需追蹤，只做一次 immutable evidence／provenance hash 檢查，不重跑或調參。
- 成功／失敗條件：所有允許的 Development bindings、seed、raw-trade digest 與摘要欄位可重核，且不讀取正式結果；任一不一致即停止 freeze。
- 不得沿用的問題：不得為了尋找更高報酬再改 stop、cooldown、訊號條件或 bootstrap 設定。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-risk2-exitcd7-seedfix-v001/manifests/preregistration.yml`
- Candidate definition：`workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-risk2-exitcd7-seedfix-v001/manifests/candidate-definition.yml`
- Development evidence：`research/fxi-deep-pullback-risk2-exitcd7-seedfix-v001/development.yml`
- 程式／測試：`src/trading_2026_2/fxi_risk2_seedfix.py`、`tests/test_fxi_risk2_seedfix.py`、`research/fxi-deep-pullback-risk2-exitcd7-seedfix-v001/run_development.py`
- 詳細盲檢討：無
