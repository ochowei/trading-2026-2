# TSM：Study Development 成果卡

本檔只整理 TSM 各 Study 的 Development 階段；未包含正式 Historical Evaluation、Terminal 或交易結果。

---

# `tsm-mean-reversion-reversal-trigger--v001`：Study Development 成果卡

- Development 判定：`未完成`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：無（本分支第一份）
- 記錄日期：`2026-09-08`

## 結論

> 規格預計在 2014–2018、base 每邊 1 bps 費用／5 bps 滑價與 stress 每邊 2 bps 費用／20 bps 滑價下，測試成交量先行加上訊號日收盤高於前收的反轉觸發；但允許讀取範圍內沒有 outcome-bearing Development evidence，因此本 Study 的 Development 結果不可判定，不能支持或否證原始假說。

## 研究變更

- 研究問題或假說：TSM 收盤低於 SMA(20) 至少 2%、RSI(2)≤35 時，若前五個 session 有成交量比率≥1.25，且訊號日收盤高於前一日，是否能提升均值回歸的穩健性。
- 相較上一個 Study 只改：本分支首份候選；加入成交量先行與訊號日反轉確認。
- 保持不變或比較基準：2% risk budget、-4% stop、+4% target、15-session 持有、退場後五-session cooldown 與 SMA＋RSI baseline。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |
| Development / stress | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |

- 交易年度覆蓋：未執行（規格規劃 2014–2018）
- 失敗 gate：未執行；允許路徑沒有 Development evidence，不能填入零或推測值。
- 未執行項目與原因：整體 Development trial 未產出可核對的 evidence；因此 base、stress、年度分段與穩健性檢查均未執行。

## 主要發現

- 已確認：preregistration、candidate definition、Development runner、程式與測試均有明確路徑，但沒有可供核對的 Development evidence。
- 可能原因：Study 可能停在 source validation 或正式執行前；這只是依檔案狀態的中等強度推論，沒有 evidence 可以確認實際停止點。
- 尚不能判斷：無法判斷交易數、報酬、PF、回撤、gate 是否通過，也無法判斷來源隔離是否已完成 provenance 審計。

## 下一輪

- 建議處置：補做一次固定規格的 Development trial，不修改候選規則。
- 下一個 Study 只測：產出這個已凍結候選的完整 Development evidence 與 bindings。
- 成功／失敗條件：依 preregistration 的完整 gates 檢查完成交易、年度覆蓋、base/stress 報酬、PF 與 stress 回撤；任何 gate 失敗即否證。
- 不得沿用的問題：不得用程式存在、測試通過或輸入檔存在，代替實際 outcome-bearing evidence。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-reversal-trigger--v001/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-reversal-trigger--v001/candidate-definition.yml`
- Development evidence：無（允許路徑未找到）
- 程式／測試：`research/tsm-mean-reversion-reversal-trigger--v001/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_reversal_trigger_v001.py`、`tests/test_tsm_mean_reversion_reversal_trigger_v001.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-reversal-trigger--v002`：Study Development 成果卡

- Development 判定：`未完成`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-reversal-trigger--v001`
- 記錄日期：`2026-09-08`

## 結論

> 本 Study 延續相同的 TSM 成交量先行與收盤反轉規則，只更新 Study／candidate 的版本識別與執行程序；但允許讀取範圍內仍沒有 Development evidence，所以無法判定 base 或 stress 結果，也不能把 v002 視為已完成的重現。

## 研究變更

- 研究問題或假說：維持 SMA(20) 偏離 2%、RSI(2)≤35、五日成交量比率≥1.25、收盤高於前收的反轉觸發。
- 相較上一個 Study 只改：規格可見的主要差異是 candidate family／程序版本更新；沒有看到訊號、成本、持有期或風險規則的語義變更。
- 保持不變或比較基準：15-session 持有、退場後五-session cooldown、-4%／+4% stop-target 與相同 baseline。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |
| Development / stress | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |

- 交易年度覆蓋：未執行（規格規劃 2014–2018）
- 失敗 gate：未執行；沒有 Development evidence 可核對。
- 未執行項目與原因：base/stress metrics、年度分段、bootstrap 與 leave-one-year-out 均未產出可引用結果。

## 主要發現

- 已確認：v002 的規格仍固定同一組訊號與成本，並保留 Development runner、程式與測試路徑；結果檔不存在於允許讀取範圍。
- 可能原因：這次版本更新可能是為了修正前一份 Study 的執行或註冊問題；現有檔案不足以確認是哪一項。
- 尚不能判斷：不能判斷 v002 是否重現 v001，也不能判斷任何 gate、provenance 或候選 freeze 狀態。

## 下一輪

- 建議處置：只執行一次 v002 的完整 Development trial，並保留不可變 evidence。
- 下一個 Study 只測：同一候選的 Development evidence 產出與來源綁定，不再改訊號。
- 成功／失敗條件：完整 gates 均有 actual、threshold 與 passed 值，且資料、程式、輸入 digest 一致；缺任何一項即未完成。
- 不得沿用的問題：不得把版本號更新當成策略變更，也不得以 v001 的結果代替 v002 evidence。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-reversal-trigger--v002/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-reversal-trigger--v002/candidate-definition.yml`
- Development evidence：無（允許路徑未找到）
- 程式／測試：`research/tsm-mean-reversion-reversal-trigger--v002/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_reversal_trigger_v001.py`、`tests/test_tsm_mean_reversion_reversal_trigger_v001.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-two-stage-volume-reversal--v001`：Study Development 成果卡

- Development 判定：`通過`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：無（本 two-stage 系列第一份）
- 記錄日期：`2026-09-08`

## 結論

> 在 2014–2018、base 每邊 1／5 bps、stress 每邊 2／20 bps、2% risk budget、-4%／+4% stop-target 與 15-session 持有下，本 Study 的 Development 結果支持「成交量先行加上訊號日收盤反轉」的候選假說：20 筆交易與五個交易年度剛好達標，base/stress 報酬與 PF 均為正，所有事前 gates 通過。

## 研究變更

- 研究問題或假說：TSM 低於 SMA(20) 1.5%、RSI(2)≤50 時，前五日成交量比率≥1.25 且訊號日收盤高於前收，是否能避免在下跌途中接刀。
- 相較上一個 Study 只改：本系列首份 Study；建立「量先換手＋價行止跌」兩階段條件。
- 保持不變或比較基準：下一 open 進場、退場後五-session cooldown、15-session 持有、2% risk budget 與 SMA＋RSI baseline。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 20 | 19.76% | 2.760 | 3.96% | 通過 |
| Development / stress | 20 | 14.90% | 2.315 | 4.34% | 通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：無；20 筆交易是完成交易門檻 20 的剛好邊界，其餘交易年度、報酬、PF、回撤與額外穩健性 gates 均通過。
- 未執行項目與原因：無；時間區塊重抽樣與 leave-one-year-out 均有 evidence。

## 主要發現

- 已確認：20 筆交易覆蓋五年；stress block bootstrap 正報酬比例為 97.57%／97.13%，逐年剔除後最低 stress 報酬 6.73%、PF 1.594、回撤 4.34%。
- 可能原因：成交量與收盤反轉的聯合條件可能避開部分下跌途中訊號；這是條件組合的合理解釋，尚未由單一條件消融證明。
- 尚不能判斷：交易數剛好貼著 20 筆門檻，且沒有 provenance declaration 可引用；因此不能把本次通過解讀成穩健性已充分餘裕。

## 下一輪

- 建議處置：建立有限 follow-up，單獨測試持有時間是否是主要限制。
- 下一個 Study 只測：把未觸發 stop／target 的持有期由 15 個 session 改為 10 個；訊號、成本、風險與 cooldown 不變。
- 成功／失敗條件：完成交易至少 20 筆、年度至少 3 年，base/stress 報酬大於 0、PF 高於 1.10／1.00，stress 回撤不超過 10%，並保留完整重抽樣與逐年剔除 evidence。
- 不得沿用的問題：不得把 20 筆剛好過門檻當成交易容量已被證明足夠。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v001/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v001/candidate-definition.yml`
- Development evidence：`research/tsm-mean-reversion-two-stage-volume-reversal--v001/development-evidence.yml`
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v001/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v001.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v001.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-two-stage-volume-reversal--v002`：Study Development 成果卡

- Development 判定：`通過`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v001`
- 記錄日期：`2026-09-08`

## 結論

> 在同一 2014–2018 Development 範圍與相同成本、風險、持有期和訊號規則下，本 Study 的 Development 結果支持原始候選假說：20 筆交易、19.76%／14.90% base／stress 報酬與 2.760／2.315 PF 均符合事前門檻，沒有 failed gate。

## 研究變更

- 研究問題或假說：測試 TSM 的 1.5% SMA 偏離、RSI(2)≤50、1.25 倍成交量先行與收盤高於前收的兩階段反轉。
- 相較上一個 Study 只改：candidate family 與 Study／實作版本更新；preregistration 沒有顯示訊號、執行或成本語義變更。
- 保持不變或比較基準：15-session 持有、退場後五-session cooldown、2% risk budget、-4%／+4% stop-target 與相同 baseline。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 20 | 19.76% | 2.760 | 3.96% | 通過 |
| Development / stress | 20 | 14.90% | 2.315 | 4.34% | 通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：無；全部事前 Development gates 通過。
- 未執行項目與原因：無；完整 Development evidence 已產出。

## 主要發現

- 已確認：本 Study evidence 的 base/stress metrics、年度覆蓋與 bootstrap／leave-one-year-out 數值完整，兩套成本下均通過。
- 可能原因：結果與前一版規格一致，較像版本化與程序重發行的確認，而不是新策略條件帶來的增量；這是檔案語義的判讀，不是額外效果估計。
- 尚不能判斷：沒有 provenance declaration，因此來源潔淨狀態不能只靠 evidence 欄位推定；同規則重發也沒有回答持有期或成交量條件的因果問題。

## 下一輪

- 建議處置：停止同規則重發，若要繼續只建立一個明確的持有期變更 Study。
- 下一個 Study 只測：將固定持有期由 15 個 session 改為 10 個，其他設定不動。
- 成功／失敗條件：沿用完整 Development gates，並要求交易數不低於 20、stress 回撤不超過 10%；任一未達即停止。
- 不得沿用的問題：不得以 v001／v002 的重複結果冒充對訊號條件的獨立驗證。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v002/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v002/candidate-definition.yml`
- Development evidence：`research/tsm-mean-reversion-two-stage-volume-reversal--v002/development-evidence.yml`
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v002/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v002.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v002.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-two-stage-volume-reversal--v003`：Study Development 成果卡

- Development 判定：`通過`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v002`
- 記錄日期：`2026-09-08`

## 結論

> 在同一 2014–2018 Development 資料與相同 15-session 兩階段反轉規則下，本 Study 的 Development 結果支持原始假說：base/stress 分別有 20 筆完成交易、19.76%／14.90% 報酬與 2.760／2.315 PF，最大回撤 3.96%／4.34%，全部事前 gates 通過。

## 研究變更

- 研究問題或假說：維持 TSM 1.5% SMA 偏離、RSI(2)≤50、1.25 倍成交量先行與收盤高於前收的兩階段反轉條件。
- 相較上一個 Study 只改：candidate family 與版本識別更新；未見策略訊號、成本或執行規則變更。
- 保持不變或比較基準：下一 open 進場、15-session 持有、退場後五-session cooldown、2% risk budget 與 -4%／+4% stop-target。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 20 | 19.76% | 2.760 | 3.96% | 通過 |
| Development / stress | 20 | 14.90% | 2.315 | 4.34% | 通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：無；全部事前 Development gates 通過。
- 未執行項目與原因：無

## 主要發現

- 已確認：evidence 具有 20 筆交易、五年分段、50,000 次 block bootstrap 與 leave-one-year-out 結果；stress 逐年剔除後最低 PF 1.594、最低報酬 6.73%。
- 可能原因：本輪沒有實質策略變更，因此通過主要表示這個版本的 Development 產出可用；不能把它解讀成新的條件增益。
- 尚不能判斷：來源 provenance 未有獨立 declaration，且 20 筆仍是交易數下限；交易容量與條件因果仍未被解開。

## 下一輪

- 建議處置：停止同規則版本化，改做一個明確的持有期變更測試。
- 下一個 Study 只測：將未觸發 stop／target 的持有期由 15 個 session 改為 10 個。
- 成功／失敗條件：沿用相同訊號、成本、風險與 cooldown；完成交易至少 20、stress 報酬大於 0、PF>1、回撤≤10%，並完成 bootstrap／leave-one-year-out。
- 不得沿用的問題：不得用重複版本的相同 metrics 宣稱 holding period、volume 或 price confirmation 已各自被證明。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v003/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v003/candidate-definition.yml`
- Development evidence：`research/tsm-mean-reversion-two-stage-volume-reversal--v003/development-evidence.yml`
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v003/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v003.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v003.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-two-stage-volume-reversal--v004`：Study Development 成果卡

- Development 判定：`未完成`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v003`
- 記錄日期：`2026-09-08`

## 結論

> 本 Study 預先登記的唯一策略變更是把固定持有期由 15 個 session 改為 10 個，目的是測試均值回歸優勢是否會隨時間衰減；然而允許讀取範圍內沒有 Development evidence，因此無法判定這個變更是否改善交易容量、報酬或風險。

## 研究變更

- 研究問題或假說：維持 1.5% SMA 偏離、RSI(2)≤50、1.25 倍成交量先行與收盤反轉，只把未觸發 stop／target 的持有期縮短至 10 個 session。
- 相較上一個 Study 只改：持有期 15→10 個 session；成本、部位、cooldown、stop／target 與訊號固定。
- 保持不變或比較基準：同一 SMA＋RSI baseline 也採 10-session 執行規則。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |
| Development / stress | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |

- 交易年度覆蓋：未執行（規格規劃 2014–2018）
- 失敗 gate：未執行；沒有 evidence 可提供 actual／threshold。
- 未執行項目與原因：未找到 Development evidence；不能以 v003 的結果代填 v004。

## 主要發現

- 已確認：v004 的 preregistration 與程式／測試明確表達 10-session time-decay 變更，但沒有結果檔。
- 可能原因：Study 可能在執行前或 source validation 階段停止；沒有允許證據可以確認。
- 尚不能判斷：無法判斷 10-session 是否增加交易數、是否造成較多成本、或是否改善 stress 回撤與 PF。

## 下一輪

- 建議處置：先完成固定規格的 Development evidence，再決定是否保留 time-decay 假說。
- 下一個 Study 只測：只執行 v004 已凍結的 10-session 持有規則，不再改門檻。
- 成功／失敗條件：完成交易至少 20、交易年度至少 3 年、base/stress 報酬大於 0、PF 高於 1.10／1.00、stress 回撤≤10%；缺 evidence 或任一 gate 失敗均不通過。
- 不得沿用的問題：不得用前一版 15-session 結果推論 10-session 的效果。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v004/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v004/candidate-definition.yml`
- Development evidence：無（允許路徑未找到）
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v004/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v004.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v004.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-two-stage-volume-reversal--v005`：Study Development 成果卡

- Development 判定：`未完成`
- Provenance（來源可信狀態）：`verified-clean`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v004`
- 記錄日期：`2026-09-08`

## 結論

> v005 延續 10-session time-decay 規格，且已有 Development authorization 與 verified-clean provenance declaration；但允許讀取範圍內沒有 outcome-bearing Development evidence。因此本 Study 尚未完成，不能判定 10-session 持有是否通過任何 base／stress gate。

## 研究變更

- 研究問題或假說：測試 10-session 固定持有是否比長持有更能保留均值回歸優勢。
- 相較上一個 Study 只改：規格中未見訊號、成本、風險或持有語義變更，主要是 Study／candidate 版本與來源登錄更新。
- 保持不變或比較基準：1.5% SMA 偏離、RSI(2)≤50、成交量比率≥1.25、收盤高於前收、10-session 持有、五-session cooldown、2% risk budget。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |
| Development / stress | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |

- 交易年度覆蓋：未執行（規格規劃 2014–2018）
- 失敗 gate：未執行；没有 Development actual 可核對。
- 未執行項目與原因：沒有 Development evidence；authorization 與 provenance 只能證明流程聲明，不能代替結果。

## 主要發現

- 已確認：v005 已有 development-only authorization、network access=false 與 verified-clean provenance，但沒有 metrics 或 gates evidence。
- 可能原因：可能是執行尚未完成或 evidence 尚未封存；目前沒有資料判定是哪一種。
- 尚不能判斷：不能判斷交易數、年度覆蓋、報酬、PF、回撤或 time-decay 假說是否成立。

## 下一輪

- 建議處置：完成 v005 的固定規格 Development evidence，或明確封存為未完成，不再用新版本掩蓋缺口。
- 下一個 Study 只測：同一 10-session 候選的 evidence 完整性與 gate 產出。
- 成功／失敗條件：base/stress 的 actual、threshold、passed、raw-trade bindings 與 provenance 均齊全；完整 gates 全數通過才算完成。
- 不得沿用的問題：不得把 authorization／provenance 通過誤寫成策略 Development 通過。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v005/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v005/candidate-definition.yml`
- Development evidence：無（允許路徑未找到）
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v005/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v005.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v005.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-two-stage-volume-reversal--v006`：Study Development 成果卡

- Development 判定：`未完成`
- Provenance（來源可信狀態）：`verified-clean`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v005`
- 記錄日期：`2026-09-08`

## 結論

> v006 仍是 10-session time-decay 候選，已有 development-only authorization 與 verified-clean provenance，但允許讀取範圍內沒有 Development evidence。故本 Study 的 Development 結果不可判定，不能填入任何交易數、報酬或 PF，也不能假設它已重現 v005 的規格。

## 研究變更

- 研究問題或假說：確認 10-session 持有規則在成交量先行與訊號日反轉條件下，是否仍能通過穩健性 gates。
- 相較上一個 Study 只改：未見策略語義變更；主要是版本、source bundle 與程序登錄更新。
- 保持不變或比較基準：1.5% SMA 偏離、RSI(2)≤50、成交量比率≥1.25、收盤高於前收、10-session 持有、五-session cooldown 與 2% risk budget。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |
| Development / stress | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |

- 交易年度覆蓋：未執行（規格規劃 2014–2018）
- 失敗 gate：未執行；沒有 outcome-bearing evidence。
- 未執行項目與原因：缺少 Development evidence；不得以 v005 或其他 Study 結果代填。

## 主要發現

- 已確認：v006 的 authorization 限定 warmup-only／development，且 network access=false；但這只描述執行範圍，沒有實際結果。
- 可能原因：版本可能尚未完成 runner 執行或封存；原因無法由允許資料確認。
- 尚不能判斷：不能判斷 10-session 規則是否改善交易數、成本後報酬、PF 或回撤，也不能判斷 v006 與 v005 是否真正重現。

## 下一輪

- 建議處置：只補齊 v006 的 Development evidence，完成後再決定是否進行 volume filter 的消融。
- 下一個 Study 只測：固定 10-session 規則下，關閉成交量先行條件；其他訊號與執行規則不變。
- 成功／失敗條件：先要求 v006 evidence 完整；後續消融版本仍須通過完成交易、年度、報酬、PF、stress 回撤與重抽樣 gates。
- 不得沿用的問題：不得把缺少 evidence 解讀成策略失敗，也不得把 authorization 當成通過。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v006/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v006/candidate-definition.yml`
- Development evidence：無（允許路徑未找到）
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v006/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v006.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v006.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-two-stage-volume-reversal--v007`：Study Development 成果卡

- Development 判定：`通過`
- Provenance（來源可信狀態）：`verified-clean`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v006`
- 記錄日期：`2026-09-08`

## 結論

> 在 2014–2018、10-session 持有、2% risk budget 與固定 base／stress 成本下，本 Study 的 Development 結果支持「只保留訊號日收盤高於前收、移除成交量先行條件」的候選可行性：25 筆交易、30.97%／23.96% 報酬、3.861／3.249 PF 與約 2.0% 回撤，所有事前 gates 通過。

## 研究變更

- 研究問題或假說：相較 v006，只移除前五個 session 的成交量尖峰條件，保留收盤高於前收的止跌確認，檢查成交量是否提供可重現的額外篩選。
- 相較上一個 Study 只改：關閉 volume-lead filter；10-session 持有與其他條件固定。
- 保持不變或比較基準：SMA(20) 偏離 1.5%、RSI(2)≤50、五-session cooldown、-4%／+4% stop-target、2% risk budget。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 25 | 30.97% | 3.861 | 2.03% | 通過 |
| Development / stress | 25 | 23.96% | 3.249 | 2.12% | 通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：無；25≥20，stress 單筆最大虧損 2.02%、bootstrap 正報酬比例最低 99.996%、逐年剔除 gates 全部通過。
- 未執行項目與原因：無；四組 mechanism ablation 只作事前固定的描述性診斷，不參與 candidate selection。

## 主要發現

- 已確認：price-only candidate 的 25 筆交易在五年內通過所有正式 gates；同一 evidence 的描述性消融顯示 volume-only 有 36 筆但 stress PF 1.280、stress 報酬 6.95%。
- 可能原因：成交量條件可能增加樣本但未必改善成本後品質；這是本 Study 內描述性消融支持的弱推論，不能外推成成交量永遠無用。
- 尚不能判斷：消融不參與選擇，且本 Study 沒有把成交量門檻做逐一控制；因此不能判斷「移除 volume」與「price-only」的因果優勢是否跨資料仍成立。

## 下一輪

- 建議處置：建立有限 follow-up，重新加入成交量條件但只改一個門檻。
- 下一個 Study 只測：在保留收盤反轉與 10-session 執行的前提下，將成交量比率門檻由 1.25 改為 1.05。
- 成功／失敗條件：沿用完整 Development gates；完成交易至少 20、stress 報酬與 PF 仍通過、回撤≤10%，並保留同樣的 mechanism ablation。
- 不得沿用的問題：不得用描述性 volume-only 結果直接選出新的成交量門檻。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v007/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v007/candidate-definition.yml`
- Development evidence：`research/tsm-mean-reversion-two-stage-volume-reversal--v007/development-evidence.yml`
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v007/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v007.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v007.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-two-stage-volume-reversal--v008`：Study Development 成果卡

- Development 判定：`未完成`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v007`
- 記錄日期：`2026-09-08`

## 結論

> 本 Study 只把成交量先行條件重新開啟，並把五日成交量門檻由 1.25 調為 1.05；然而允許讀取範圍內沒有 Development evidence。即使規格已固定 10-session 持有與相同成本，本 Study 仍未完成，不能判定交易數、報酬、PF 或風險是否改善。

## 研究變更

- 研究問題或假說：在保留收盤反轉的前提下，較寬鬆的 1.05 倍成交量確認能否增加交易樣本並維持風險調整後品質。
- 相較上一個 Study 只改：重新啟用 volume-lead，且門檻 1.25→1.05；其他訊號與 10-session 執行固定。
- 保持不變或比較基準：SMA(20) 偏離 1.5%、RSI(2)≤50、收盤高於前收、五-session cooldown、2% risk budget、-4%／+4% stop-target。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |
| Development / stress | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |

- 交易年度覆蓋：未執行（規格規劃 2014–2018）
- 失敗 gate：未執行；沒有 Development evidence 可核對。
- 未執行項目與原因：base/stress、年度、重抽樣與 mechanism ablation 均未產出 evidence。

## 主要發現

- 已確認：v008 已有 development-only authorization、固定成本與輸入規格，但允許路徑只看得到程式／測試與程序檔，沒有結果 evidence。
- 可能原因：可能尚未完成 runner 或封存；現有資料不能確認執行阻塞點。
- 尚不能判斷：不能判斷 1.05 門檻是否真的增加交易數，也不能判斷新增交易是否帶來成本後的改善或更大回撤。

## 下一輪

- 建議處置：先完成 v008 的固定規格 Development evidence。
- 下一個 Study 只測：不再改 1.05 門檻或訊號，補齊實際 run、raw trades、metrics、gates 與 provenance bindings。
- 成功／失敗條件：完整 Development gates 通過，並能核對 volume-on 與 price-only 的描述性消融；缺任何 evidence 或 gate 失敗都不進 freeze。
- 不得沿用的問題：不得使用規格中的預期交易數或前一版結果代替 v008 actual。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v008/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v008/candidate-definition.yml`
- Development evidence：無（允許路徑未找到）
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v008/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v008.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v008.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-two-stage-volume-reversal--v009`：Study Development 成果卡

- Development 判定：`通過`
- Provenance（來源可信狀態）：`verified-clean`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v008`
- 記錄日期：`2026-09-08`

## 結論

> 在 2014–2018、1.05 倍成交量先行、收盤反轉、10-session 持有、2% risk budget 與固定 base／stress 成本下，本 Study 的 Development 結果支持校準後 two-stage candidate 的可行性：24 筆交易、33.68%／26.52% 報酬、5.036／4.204 PF 與 2.00%／2.12% 回撤，所有 formal gates 通過。

## 研究變更

- 研究問題或假說：在保留 1.5% SMA 偏離、RSI(2)≤50 與訊號日收盤反轉下，把成交量先行門檻固定為 1.05，檢查適度換手條件是否保留樣本與穩健性。
- 相較上一個 Study 只改：確認並重發 1.05 倍 volume-lead candidate 的可核對 Development evidence；本輪規格的策略門檻維持 1.05。
- 保持不變或比較基準：10-session 持有、五-session cooldown、-4%／+4% stop-target、2% risk budget 與相同資料邊界。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 24 | 33.68% | 5.036 | 2.00% | 通過 |
| Development / stress | 24 | 26.52% | 4.204 | 2.12% | 通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：無；stress block bootstrap 正報酬比例最低 99.998%、stress 回撤超過 10% 比例為 0，逐年剔除後最低 stress 報酬 18.36%、PF 3.409。
- 未執行項目與原因：無；evidence 另含事前固定、非選擇用途的 mechanism ablation。

## 主要發現

- 已確認：24 筆交易分布於五年，兩套成本下均通過 formal gates；描述性消融中的 price-only 有 24 筆，而 calibrated two-stage 有 25 筆，兩者均有正 stress 結果。
- 可能原因：1.05 門檻可能在交易容量與篩選強度間取得平衡；這是同一 Development evidence 的合理解釋，不代表門檻已被最佳化證明。
- 尚不能判斷：消融不是 candidate selection，且 24 筆仍是有限樣本；無法由本卡判斷 1.05 是否優於所有其他門檻。

## 下一輪

- 建議處置：若要增加容量，只允許一次單參數變更，並保留本 Study 作固定基準。
- 下一個 Study 只測：只把退場後 cooldown 由 5 個 session 改為 3 個，維持 1.5%／RSI 50／volume 1.05 與 10-session 持有。
- 成功／失敗條件：完成交易增加但不少於 20，base/stress 報酬與 PF 通過，stress 回撤≤10%，bootstrap 與 leave-one-year-out gates 不得退化失敗。
- 不得沿用的問題：不得同時放寬 SMA 偏離、RSI 與 cooldown，否則無法知道容量變化由哪一個設定造成。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v009/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v009/candidate-definition.yml`
- Development evidence：`research/tsm-mean-reversion-two-stage-volume-reversal--v009/development.yml`
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v009/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v009.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-two-stage-volume-reversal--v010`：Study Development 成果卡

- Development 判定：`通過`
- Provenance（來源可信狀態）：`verified-clean`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v009`
- 記錄日期：`2026-09-08`

## 結論

> 在 2014–2018 與相同成本、風險及 10-session 持有下，本 Study 的 Development 結果支持「提高交易容量的參數組合」通過既定 Development gates：base/stress 各 29 筆交易，報酬 34.79%／26.59%，PF 3.837／3.206，最大回撤 2.55%／2.58%。但本輪同時改了三個設定，效果不能歸因到單一參數。

## 研究變更

- 研究問題或假說：把 SMA 偏離門檻由 1.5% 放寬至 1.2%、RSI 上限由 50 放寬至 55，並把退場後 cooldown 由 5 縮短至 3，檢查交易容量能否增加而不破壞成本後品質。
- 相較上一個 Study 只改：一個「容量擴張組合」同時改三項設定；這不是可完全歸因於單一 knob 的變更。
- 保持不變或比較基準：volume 1.05、收盤高於前收、10-session 持有、2% risk budget、-4%／+4% stop-target 與相同資料。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 29 | 34.79% | 3.837 | 2.55% | 通過 |
| Development / stress | 29 | 26.59% | 3.206 | 2.58% | 通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：無；stress PF 為 3.206、stress 報酬 26.59%，且 bootstrap、逐年剔除、單筆損失與回撤 gates 均通過。
- 未執行項目與原因：無；mechanism ablation 為事前固定的描述性診斷。

## 主要發現

- 已確認：29 筆交易覆蓋五年，stress block bootstrap 正報酬比例 99.972%／99.960%，逐年剔除後最低 stress 報酬 16.89%、PF 2.652。
- 可能原因：放寬入場範圍與縮短 cooldown 共同增加了交易機會；由於三項設定同時改變，這只能是組合效果的推論。
- 尚不能判斷：無法知道較寬 SMA、較寬 RSI 或較短 cooldown 哪一項主導交易數與結果；若要再調整，應先拆開驗證。

## 下一輪

- 建議處置：建立單參數隔離 follow-up，不再複製三項同時放寬。
- 下一個 Study 只測：固定 1.2% SMA、RSI 55、volume 1.05 與 10-session 持有，只把 cooldown 由 3 恢復為 5 個 session。
- 成功／失敗條件：完整 gates 通過，並比較交易數、stress 報酬、PF 與回撤；任何 gate 失敗即否證該單一 cooldown 變更。
- 不得沿用的問題：不得把 v010 的通過結果歸因於其中任何一個設定，也不得再同時修改 SMA、RSI、cooldown。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v010/candidate-definition.yml`
- Development evidence：`research/tsm-mean-reversion-two-stage-volume-reversal--v010/development.yml`
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v010/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v010.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v010.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-two-stage-volume-reversal--v011`：Study Development 成果卡

- Development 判定：`未完成`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v010`
- 記錄日期：`2026-09-08`

## 結論

> 本 Study 的唯一核心主張是把跌深資格與止跌確認拆成兩階段：資格建立後最多保留三個交易日，第一次收盤高於前收且仍低於 SMA(20) 才在下一 open 進場；但允許讀取範圍內沒有 Development evidence。因此無法判定它是否真的增加交易數、改善 stress 報酬，或新增交易的成本後損益是否為正。

## 研究變更

- 研究問題或假說：以 1.5% SMA 偏離、RSI(2)≤50、volume 1.05 建立資格，保留 v009 同日確認，並允許三日內延後確認。
- 相較上一個 Study 只改：改回 v009 的嚴格資格門檻，加入三日有效期的 delayed confirmation 與明確等待狀態；這是機制變更，不是單純參數調整。
- 保持不變或比較基準：10-session 持有、2% risk budget、-4%／+4% stop-target、資料邊界與 base／stress 成本固定。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |
| Development / stress | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |

- 交易年度覆蓋：未執行（規格規劃 2014–2018）
- 失敗 gate：未執行；三項 research targets 也沒有 actual evidence 可核對。
- 未執行項目與原因：沒有 Development evidence；不能以 v009／v010 的結果填入交易數或比較目標。

## 主要發現

- 已確認：preregistration 固定資格期限、等待衝突順序、v009／v010 reference controls 與新增交易損益目標，但沒有 outcome-bearing evidence。
- 可能原因：Study 可能尚未執行或結果尚未封存；檔案狀態不能確認原因。
- 尚不能判斷：不能判斷 delayed confirmation 是否增加有效交易、是否稀釋 PF，或新增交易在兩套成本下是否合計為正。

## 下一輪

- 建議處置：只完成 v011 的固定規格 Development trial，再依事前 targets 決定停止或 freeze。
- 下一個 Study 只測：產出延後確認版本的完整 raw trades、v009／v010 controls 與新增交易比較；不調整三日有效期。
- 成功／失敗條件：交易數嚴格高於 29、stress 報酬嚴格高於 v009、延後新增交易的 base 與 stress 合計損益都大於 0，且 formal gates 全數通過。
- 不得沿用的問題：不得先看結果再放寬資格期限、門檻或比較條件。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v011/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v011/candidate-definition.yml`
- Development evidence：無（允許路徑未找到）
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v011/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v011.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v011.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-two-stage-volume-reversal--v012`：Study Development 成果卡

- Development 判定：`未通過`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v011`
- 記錄日期：`2026-09-08`

## 結論

> 在 2014–2018、1.5% SMA 偏離、RSI(2)≤50、volume 1.05、10-session 持有與相同成本下，本 Study 的 Development 結果不支持同日盤中反轉確認的候選 freeze：base/stress 雖仍為正報酬，但只有 28 筆交易，stress PF 1.849、stress 報酬 15.38%，均低於本輪預先固定的選擇門檻。

## 研究變更

- 研究問題或假說：保留 v009 的超跌、RSI 與成交量資格；若當日收盤高於開盤、日內 high>low，且收盤位於當日區間上方三分之一，即使未高於前收也提早確認反轉。
- 相較上一個 Study 只改：移除三日 delayed confirmation，改為同日盤中反轉條件；同時使用較嚴格的交易數、stress PF 與 stress 報酬選擇門檻。
- 保持不變或比較基準：下一日 open 進場、10-session 持有、五-session cooldown、2% risk budget、-4%／+4% stop-target 與相同資料。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 28 | 21.80% | 2.166 | 5.88% | 未通過 |
| Development / stress | 28 | 15.38% | 1.849 | 5.88% | 未通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：`completed_trades` 28≥30 失敗；`stress_profit_factor` 1.84883≥3.20558 失敗；`stress_return` 0.15380>0.26590 失敗。
- 未執行項目與原因：正式 Development evidence 有產出；未通過後不應進入候選 freeze，也不延伸執行後段結果。

## 主要發現

- 已確認：候選在兩套成本下仍有正報酬，但交易數、stress PF 與 stress 報酬都未達本輪事前門檻；stress bootstrap 正報酬比例約 93.76%／95.92%，並不能抵銷上述 failed gates。
- 可能原因：同日盤中條件可能替換了原 v009 的交易路徑，造成新增或被排擠交易的成本後品質下降；這需要 evidence 內的交易比較才能進一步拆解，不能只看 aggregate metrics。
- 尚不能判斷：目前不能判斷失敗主要來自盤中確認規則、交易替換，或本輪提高的 selection floor；也不能把正報酬解讀成假說通過。

## 下一輪

- 建議處置：停止本次 intraday-reversal 假說，不放寬 failed gates。
- 下一個 Study 只測：若仍需 follow-up，只恢復 v009 的收盤高於前收確認，其他 1.5%／RSI 50／volume 1.05／10-session 設定固定。
- 成功／失敗條件：必須重新通過本輪的交易數、stress PF、stress 報酬與原有穩健性 gates；任一失敗即停止，不再加入第三種確認規則。
- 不得沿用的問題：不得因候選仍有正報酬就降低 30 筆、PF 3.20558 或 stress 報酬 0.26590 的事前門檻。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v012/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v012/candidate-definition.yml`
- Development evidence：`research/tsm-mean-reversion-two-stage-volume-reversal--v012/evidence/development.yml`
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v012/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v012.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v012.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-volume-lead-setup--v003`：Study Development 成果卡

- Development 判定：`未完成`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-reversal-trigger--v002`
- 記錄日期：`2026-09-08`

## 結論

> 本 Study 測試的是移除訊號日收盤方向條件、只保留前五日成交量先行的 TSM setup；但允許讀取範圍內沒有 Development evidence。因而不能判定放寬方向條件是否增加可交易樣本、維持成本後報酬，或改善跨年度穩健性。

## 研究變更

- 研究問題或假說：TSM 低於 SMA(20) 至少 2%、RSI(2)≤35 且前五日成交量比率≥1.25 時，即使訊號日未收紅，是否仍保留有參與度的回落 setup。
- 相較上一個 Study 只改：移除 `close_above_prior_close` 方向確認；成交量先行與其他執行規則固定。
- 保持不變或比較基準：15-session 持有、五-session cooldown、2% risk budget、-4%／+4% stop-target、base／stress 成本與 SMA＋RSI baseline。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |
| Development / stress | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |

- 交易年度覆蓋：未執行（規格規劃 2014–2018）
- 失敗 gate：未執行；缺少 Development evidence。
- 未執行項目與原因：base/stress metrics、年度分段、bootstrap 與 leave-one-year-out 均沒有 actual。

## 主要發現

- 已確認：v003 的候選、runner、程式與測試明確保留 volume-lead 並關閉方向確認，但沒有可核對的結果檔。
- 可能原因：Study 可能停在正式 trial 前；這是檔案狀態推論，不能當作執行原因。
- 尚不能判斷：無法判斷不加方向條件會增加多少交易，也不能判斷新增交易是改善還是稀釋 stress PF。

## 下一輪

- 建議處置：先完成 v003 固定規格 Development evidence，再決定是否停止或保留 setup 假說。
- 下一個 Study 只測：只執行「volume lead、無訊號日方向確認」版本，不再改 RSI、SMA 偏離或持有期。
- 成功／失敗條件：完整 Development gates、交易年度、兩套成本報酬與 PF、stress 回撤及重抽樣均需有 actual 並通過。
- 不得沿用的問題：不得以同系列有方向確認的 Study 結果代替本候選的實際 evidence。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-lead-setup--v003/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-volume-lead-setup--v003/candidate-definition.yml`
- Development evidence：無（允許路徑未找到）
- 程式／測試：`research/tsm-mean-reversion-volume-lead-setup--v003/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_volume_lead_setup_v003.py`、`tests/test_tsm_mean_reversion_volume_lead_setup_v003.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-volume-leads--v001`：Study Development 成果卡

- Development 判定：`不可判定`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：無（volume-leads 分支第一份）
- 記錄日期：`2026-09-08`

## 結論

> 這份 Study 原本要測試 TSM 的 volume-lead 均值回歸候選，但 Development authorization 後，允許資料明確記錄 source validation 在產出 outcome-bearing trial 前失敗，且 current frozen setup 已關閉。因此本 Study 沒有可判定的 Development 結果，不支持也不否證原始假說。

## 研究變更

- 研究問題或假說：SMA(20) 偏離至少 2%、RSI(2)≤35 時，若前五日成交量比率≥1.25，能否在價格偏離擴大前辨識換手並提高均值回歸穩健性。
- 相較上一個 Study 只改：本分支首份候選；加入 volume-lead 條件。
- 保持不變或比較基準：15-session 持有、五-session cooldown、2% risk budget、-4%／+4% stop-target 與 base／stress 成本。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 未執行 | 未執行 | 未執行 | 未執行 | 不可判定 |
| Development / stress | 未執行 | 未執行 | 未執行 | 未執行 | 不可判定 |

- 交易年度覆蓋：未執行（規格規劃 2014–2018）
- 失敗 gate：不可判定；沒有 outcome-bearing trial，不能視為通過或 failed gate。
- 未執行項目與原因：`evidence-unavailable` 記錄 source validation 在 Development outcome 產出前失敗；現有 frozen setup 關閉，應建立修正 Study。

## 主要發現

- 已確認：Development authorization 存在，但明確的 evidence-unavailable payload 說明沒有產出結果試驗；因此沒有任何 base/stress actual。
- 可能原因：來源驗證未通過，可能涉及 snapshot 或 source binding；這裡只記錄 evidence 已明示的狀態，不猜測具體技術原因。
- 尚不能判斷：無法判斷 volume-lead 規則的交易數、報酬、PF、回撤或 provenance 是否能成立。

## 下一輪

- 建議處置：建立 corrected Study，只修正 source validation／snapshot integrity，不修改 volume-lead 策略。
- 下一個 Study 只測：讓同一候選產出可核對的 warmup、Development raw trades、metrics 與 bindings。
- 成功／失敗條件：source validation、network control、資料 digest 與完整 Development gates 全數有證據；若仍無 outcome-bearing evidence，維持未完成。
- 不得沿用的問題：不得用 v001 的空缺當作策略失敗，也不得把修正 Study 的結果回填覆寫本 Study。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-leads--v001/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-volume-leads--v001/candidate-definition.yml`
- Development evidence：`research/tsm-mean-reversion-volume-leads--v001/evidence-unavailable.payload.yml`（無 outcome-bearing evidence）
- 程式／測試：`research/tsm-mean-reversion-volume-leads--v001/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_volume_leads.py`、`tests/test_tsm_mean_reversion_volume_leads.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-volume-leads--v002`：Study Development 成果卡

- Development 判定：`未通過`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-volume-leads--v001`
- 記錄日期：`2026-09-08`

## 結論

> 在 2014–2018、SMA(20) 偏離 2%、RSI(2)≤35、volume-lead 比率≥1.25、15-session 持有與固定成本下，本 Study 的 Development 結果不支持穩健的 volume-lead 假說：aggregate stress 報酬仍為 2.03%，但四個穩健性 gates 失敗，包含 bootstrap 正報酬比例、回撤超標比例，以及 leave-one-year-out 的 PF 與報酬。

## 研究變更

- 研究問題或假說：修正 v001 的來源驗證問題後，測試不含訊號日方向確認的 volume-lead candidate 是否能在五年中維持穩健均值回歸。
- 相較上一個 Study 只改：修正 source／程序版本以產出正式 Development evidence；訊號仍是 volume-lead 1.25，沒有加入方向確認。
- 保持不變或比較基準：2% risk budget、-4%／+4% stop-target、15-session 持有、五-session cooldown、base／stress 成本與相同 baseline。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 29 | 6.86% | 1.294 | 6.40% | 未通過 |
| Development / stress | 29 | 2.03% | 1.088 | 6.77% | 未通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：stress block bootstrap 回撤超標比例 0.25024／0.20438>0.10；正報酬比例 0.60006／0.61252<0.80；leave-one-year-out 最低 PF 0.96755≤1；最低報酬 -0.00459≤0。
- 未執行項目與原因：正式 evidence 有產出；因穩健性 gates 失敗，不進入候選 freeze。

## 主要發現

- 已確認：aggregate base/stress 報酬與 PF 為正，但 stress block bootstrap 的正報酬比例最高只有 61.25%，且某些逐年剔除路徑出現負報酬與 PF<1。
- 可能原因：只用成交量先行而沒有價格方向確認，可能保留較多不完整的回落 setup；這是結果型態支持的合理解釋，不能當成已證明的因果機制。
- 尚不能判斷：無法由本 Study 單獨判斷失敗來自 volume threshold、缺少方向確認，或該均值回歸 setup 本身；provenance 也沒有獨立 declaration 可補強。

## 下一輪

- 建議處置：建立有限 follow-up，只加入訊號日收盤低於前收的方向確認，不改 volume threshold。
- 下一個 Study 只測：在 1.25 volume-lead 與其他設定固定下，新增 `close_below_prior_close`。
- 成功／失敗條件：完整原有 gates 全數通過，尤其 stress bootstrap 正報酬比例≥80%、回撤超標比例≤10%，以及 leave-one-year-out 的最低 PF>1、報酬>0。
- 不得沿用的問題：不得因 aggregate 報酬為正而忽略路徑穩健性 failed gates。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-leads--v002/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-volume-leads--v002/candidate-definition.yml`
- Development evidence：`research/tsm-mean-reversion-volume-leads--v002/development.yml`
- 程式／測試：`research/tsm-mean-reversion-volume-leads--v002/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_volume_leads.py`、`tests/test_tsm_mean_reversion_volume_leads.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-volume-leads--v003`：Study Development 成果卡

- Development 判定：`未通過`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-volume-leads--v002`
- 記錄日期：`2026-09-08`

## 結論

> 在同一 2014–2018 資料、1.25 volume-lead 與固定成本下，本 Study 新增訊號日收盤低於前收的方向確認後，仍未支持穩健的 volume-lead 假說：base/stress 報酬降至 4.42%／0.01%，stress PF 僅 1.0003，且四個路徑穩健性 gates 再次失敗。

## 研究變更

- 研究問題或假說：成交量先行若再加上訊號日收盤低於前收，是否能把較有方向的回落 setup 與無方向成交量異常分開。
- 相較上一個 Study 只改：新增 `close_below_prior_close`；SMA 偏離 2%、RSI(2)≤35、volume 1.25、成本、風險、持有期與 cooldown 固定。
- 保持不變或比較基準：15-session 持有、2% risk budget、-4%／+4% stop-target、base／stress 成本與相同 SMA＋RSI baseline。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 28 | 4.42% | 1.191 | 6.40% | 未通過 |
| Development / stress | 28 | 0.01% | 1.000 | 8.09% | 未通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：stress bootstrap 回撤超標比例 0.34794／0.27364>0.10；正報酬比例 0.50224／0.50444<0.80；leave-one-year-out 最低 PF 0.82576≤1、最低報酬 -0.02431≤0。
- 未執行項目與原因：正式 evidence 有產出；因 failed gates 不進入 candidate freeze。

## 主要發現

- 已確認：加入方向條件後，stress aggregate 報酬接近零，且 2015、2017、2018 的 leave-one-year-out stress 報酬或 PF 低於門檻；四個既定穩健性 gates 全部失敗。
- 可能原因：新增方向條件可能排除部分可盈利交易，卻沒有充分排除下行風險；這是觀察到的結果型態，不能單獨證明機制。
- 尚不能判斷：無法從本 Study 判斷是否應移除方向條件、降低 volume threshold，或停止 volume-lead 分支；不能以幾乎零的 stress 報酬宣稱「不虧」即足夠。

## 下一輪

- 建議處置：停止本方向確認版本，不再疊加第三個 filter。
- 下一個 Study 只測：若流程必須 follow-up，只移除 `close_below_prior_close`，其餘 volume-lead 設定固定；不得同時改 threshold。
- 成功／失敗條件：必須重新通過原有 bootstrap 與 leave-one-year-out gates，且 stress 報酬、PF、回撤與交易數都達到事前門檻；否則終止此分支。
- 不得沿用的問題：不得把 stress 報酬 0.01% 視為穩健成功，也不得繼續用方向條件堆疊來掩蓋路徑失敗。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-leads--v003/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-volume-leads--v003/candidate-definition.yml`
- Development evidence：`research/tsm-mean-reversion-volume-leads--v003/development.yml`
- 程式／測試：`research/tsm-mean-reversion-volume-leads--v003/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_volume_leads_v003.py`、`tests/test_tsm_mean_reversion_volume_leads_v003.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-bollinger-rebound--v001`：Study Development 成果卡

- Development 判定：`未通過`
- Provenance（來源可信狀態）：`verified-clean`
- 前一個 Study：無（布林反彈系列第一份）
- 記錄日期：`2026-09-08`

## 結論

> 在 2014–2018、base 每邊 1 bps 費用／5 bps 滑價與 stress 每邊 2 bps 費用／20 bps 滑價下，本 Study 的 Development 結果不支持布林下軌超跌反彈候選進入 freeze：雖然 25 筆交易取得正報酬（base 27.59%／stress 20.99%）與良好獲利因子（3.766／3.088），但未能跨過事前設定的 30 筆完成交易、stress PF 3.2056 與 stress 報酬 26.59% 的較高選擇門檻，共有三個 formal gates 失敗。

## 研究變更

- 研究問題或假說：將均值回歸的超跌條件由固定均線偏離改為動態布林通道下軌（%b ≤ 0.25），並搭配前五日成交量比率 ≥ 1.05 與訊號日收盤反轉，檢驗能否改善極端行情下的進場品質。
- 相較上一個 Study 只改：本系列首份 Study；引進動態布林通道下軌作為超跌資格，同時保留成交量先行與收盤確認。
- 保持不變或比較基準：20 日、±2 倍標準差通道的布林 baseline；10-session 持有、退場後 5-session cooldown、2% risk budget、-4%／+4% stop-target 與相同成本。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 25 | 27.59% | 3.766 | 2.58% | 未通過 |
| Development / stress | 25 | 20.99% | 3.088 | 2.54% | 未通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：`completed_trades` 25 < 30 失敗；`stress_profit_factor` 3.0878 < 3.20558 失敗；`stress_return` 0.20988 < 0.26590 失敗。
- 未執行項目與原因：無；正式 Development evidence 已完整產出。

## 主要發現

- 已確認：候選在兩套成本模型下均為正報酬且最大回撤僅約 2.5%，bootstrap 正報酬比例達 99.88% 以上；但未能達成事前針對容量與超越基準所設定的較高選擇門檻。
- 可能原因：動態布林下軌加上成交量與價格反轉的三重約束過於嚴苛，大幅過濾了進場機會，致使交易樣本僅有 25 筆，限制了整體報酬積累。
- 尚不能判斷：無法確認動態布林相較於固定均線偏離的真實邊際貢獻，亦無法確定若放寬觀察窗口能否在不犧牲品質下增加交易數。

## 下一輪

- 建議處置：建立有限 follow-up，嘗試引入事件觀察期以捕捉延後確認的反彈機會。
- 下一個 Study 只測：將同日布林條件拆分為事件觸發與 5 個 session 內的延後確認，其他風險與執行規則固定。
- 成功／失敗條件：完成交易至少 30 筆，且 stress 報酬、PF 與回撤符合事前 gate；任一失敗即否證。
- 不得沿用的問題：不得因策略為正報酬就事後放寬交易數或績效門檻。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v001/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-bollinger-rebound--v001/candidate-definition.yml`
- Development evidence：`research/tsm-mean-reversion-bollinger-rebound--v001/evidence/development.yml`
- 程式／測試：`research/tsm-mean-reversion-bollinger-rebound--v001/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_bollinger_rebound_v001.py`、`tests/test_tsm_mean_reversion_bollinger_rebound_v001.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-bollinger-rebound--v002`：Study Development 成果卡

- Development 判定：`未通過`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-bollinger-rebound--v001`
- 記錄日期：`2026-09-08`

## 結論

> 在 2014–2018 與相同 base/stress 成本下，本 Study 將布林條件改為事件記憶架構後，Development 結果不支持候選假說：完成交易僅 16 筆，不僅未達研究目標（30 筆）與 Workflow gate（20 筆），且 base/stress 報酬（10.89%／7.57%）與回撤均未達事前設定之比較目標，多項候選資格 gate 失敗。

## 研究變更

- 研究問題或假說：布林下軌跌深與爆量觸發後，若在後續 5 個 session 內守住事件日低點且出現收盤反轉，是否能捕捉更多延後止跌的反彈交易並維持品質。
- 相較上一個 Study 只改：將同日條件改為「事件記憶（5 個 session 觀察期）」與「縮量守低後反轉確認」兩階段架構。
- 保持不變或比較基準：10-session 持有、退場後 5-session cooldown、2% risk budget、-4%／+4% stop-target、base（1/5 bps）與 stress（2/20 bps）成本。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 16 | 10.89% | 2.868 | 2.58% | 未通過 |
| Development / stress | 16 | 7.57% | 2.240 | 2.54% | 未通過 |

- 交易年度覆蓋：5（2014–2018，但 2017 僅 1 筆）
- 失敗 gate：`completed_trades` 16 < 20（Workflow 最低門檻）與 16 < 30 失敗；`more_completed_trades_than_v009`、`base_return_not_below_v009`、`stress_return_not_below_v009` 等事前目標均失敗。
- 未執行項目與原因：無；正式 Development evidence 已完整產出。

## 主要發現

- 已確認：事件漏斗過窄，60 個事件中高達 56.7%（34 個）在觀察期跌破事件低點失效，僅 16 個事件最終進場；且 8 筆交易以 10-session 到期平倉（time exit），顯示反轉動能未如預期展開。
- 可能原因：加入守住事件日低點的條件進一步加劇了訊號稀疏問題，使得交易機會由 v001 的 25 筆降至 16 筆；盲檢討亦指出事件到期邊界與未對齊的成交量參數可能增加過濾雜訊。
- 尚不能判斷：由於樣本過少且 2018 年少數交易貢獻近半獲利，無法由 16 筆交易判斷事件記憶結構是否具備真實因果優勢。

## 下一輪

- 建議處置：停止本事件記憶與縮量守低假說，不在此 Study 放寬門檻。
- 下一個 Study 只測：若需繼續布林研究，應簡化觸發條件或改進持有期配對，不再疊加事件觀察與守低狀態機。
- 成功／失敗條件：完成交易至少 20 筆（優先滿足流程底線），stress PF > 1.10、報酬 > 0 且通過各年度穩健性檢查。
- 不得沿用的問題：不得在未修正事件到期與未對齊參數的情況下沿用此複雜事件狀態機。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v002/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-bollinger-rebound--v002/candidate-definition.yml`
- Development evidence：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v002/evidence/development.yml`
- 程式／測試：`research/tsm-mean-reversion-bollinger-rebound--v002/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_bollinger_rebound_v002.py`、`tests/test_tsm_mean_reversion_bollinger_rebound_v002.py`
- 詳細盲檢討：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-bollinger-rebound--v002/reviews/001-first-review.md`

---

# `tsm-mean-reversion-supplemental-divergence--v001`：Study Development 成果卡

- Development 判定：`未完成`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：無（補充量價背離系列第一份）
- 記錄日期：`2026-09-08`

## 結論

> 規格預計在 2014–2018、base 每邊 1/5 bps 與 stress 每邊 2/20 bps 下，測試在原有均值回歸之外新增「量價背離補充進場路徑」的效果；但允許讀取範圍內沒有 outcome-bearing Development evidence，因此本 Study 的 Development 結果不可判定，不能支持或否證原始假說。

## 研究變更

- 研究問題或假說：TSM 在既有跌深反彈條件之外，若在低檔出現價格破底但成交量未創高的量價背離現象，補充進場能否增加有效交易機會。
- 相較上一個 Study 只改：本系列首份候選；新增量價背離補充觸發路徑（ATR 距離、近 3 日低點比對與成交量分數）。
- 保持不變或比較基準：10-session 持有、退場後 5-session cooldown、2% risk budget、-4%／+4% stop-target 與相同成本。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |
| Development / stress | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |

- 交易年度覆蓋：未執行（規格規劃 2014–2018）
- 失敗 gate：未執行；缺少 Development evidence。
- 未執行項目與原因：整體 Development trial 未產出可核對的 outcome-bearing evidence；base、stress 與各項診斷均未執行。

## 主要發現

- 已確認：規格、Development authorization、runner、策略程式與測試均存在於允許路徑，但沒有可供核對的結果 evidence。
- 可能原因：Study 可能停在驗證或授權階段，尚未正式封存 trial 結果；這是依檔案現況的推論，無法由證據證實具體停頓原因。
- 尚不能判斷：無法判斷補充背離路徑的交易數、報酬、PF、回撤或 gate 是否通過。

## 下一輪

- 建議處置：補齊固定規格的 Development trial 證據，不修改候選規則。
- 下一個 Study 只測：產出已登記候選的完整 Development evidence 與 bindings。
- 成功／失敗條件：依 preregistration 的完整 gates 檢查完成交易（至少 20 筆）、年度覆蓋、base/stress 報酬與 PF；任一 gate 失敗即否證。
- 不得沿用的問題：不得以程式或授權存在代替實際 outcome-bearing evidence。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-supplemental-divergence--v001/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-supplemental-divergence--v001/candidate-definition.yml`
- Development evidence：無（允許路徑未找到）
- 程式／測試：`research/tsm-mean-reversion-supplemental-divergence--v001/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_supplemental_divergence_v001.py`、`tests/test_tsm_mean_reversion_supplemental_divergence_v001.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-supplemental-divergence--v002`：Study Development 成果卡

- Development 判定：`未完成`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-supplemental-divergence--v001`
- 記錄日期：`2026-09-08`

## 結論

> 本 Study 延續相同的量價背離補充路徑規格，更新 Study 與 candidate 版本識別；但允許讀取範圍內仍未產出 outcome-bearing Development evidence。因此本 Study 尚未完成，無法判定補充路徑是否有效。

## 研究變更

- 研究問題或假說：維持 TSM 均線偏離 1.5%、RSI(2)≤50、成交量先行 1.05 與量價背離補充路徑的雙重觸發設計。
- 相較上一個 Study 只改：規格中僅見 candidate family 與版本識別更新；未見策略進出場、成本或風控語義變更。
- 保持不變或比較基準：10-session 持有、5-session cooldown、2% risk budget、-4%／+4% stop-target 與相同成本。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |
| Development / stress | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |

- 交易年度覆蓋：未執行（規格規劃 2014–2018）
- 失敗 gate：未執行；無 Development evidence。
- 未執行項目與原因：未產出結果檔，base、stress、年度分段與 bootstrap 均未執行。

## 主要發現

- 已確認：v002 規格與程式測試齊全，但結果檔不存在於允許路徑。
- 可能原因：可能是為了排解前一版本的執行或註冊流程問題，但仍未完成結果封存；現有資料無法斷定。
- 尚不能判斷：無法判斷策略表現、交易容量或是否通過任何事前 gates。

## 下一輪

- 建議處置：只執行一次固定規格的 Development trial 並封存 evidence，不再改動訊號。
- 下一個 Study 只測：同一量價背離候選的 Development evidence 產出。
- 成功／失敗條件：完整 gates 均有 actual 且通過門檻；缺漏任何一項即未完成。
- 不得沿用的問題：不得以版本號遞增代替實際結果。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-supplemental-divergence--v002/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-supplemental-divergence--v002/candidate-definition.yml`
- Development evidence：無（允許路徑未找到）
- 程式／測試：`research/tsm-mean-reversion-supplemental-divergence--v002/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_supplemental_divergence_v002.py`、`tests/test_tsm_mean_reversion_supplemental_divergence_v002.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-supplemental-divergence--v003`：Study Development 成果卡

- Development 判定：`未完成`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-supplemental-divergence--v002`
- 記錄日期：`2026-09-08`

## 結論

> 本 Study 再次保留相同的量價背離補充架構，進行第三次程序版本更新；但允許讀取範圍內依然缺少 Development evidence。故無法判定任何 base 或 stress 指標，本 Study 處於未完成狀態。

## 研究變更

- 研究問題或假說：確認量價背離補充路徑在 TSM 均值回歸中的表現。
- 相較上一個 Study 只改：Study 及 candidate 版本識別更新；未見訊號、成本或執行規則變更。
- 保持不變或比較基準：10-session 持有、5-session cooldown、2% risk budget、-4%／+4% stop-target 與相同成本。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |
| Development / stress | 未執行 | 未執行 | 未執行 | 未執行 | 未完成 |

- 交易年度覆蓋：未執行（規格規劃 2014–2018）
- 失敗 gate：未執行；無結果 evidence。
- 未執行項目與原因：缺少 Development evidence，不能填入任何預期值。

## 主要發現

- 已確認：v003 仍維持相同策略架構與檔案結構，但無可核對的結果檔。
- 可能原因：版本更迭可能涉及 runner 或環境調校，但尚未產生正式 evidence。
- 尚不能判斷：無法評估背離補充路徑的實際交易次數與獲利能力。

## 下一輪

- 建議處置：專注產出完整的 Development evidence，避免持續同規則重發。
- 下一個 Study 只測：產出本策略的完整 evidence 與資料綁定。
- 成功／失敗條件：完成交易至少 20 筆、stress 報酬大於 0、PF > 1.0、最大回撤在限度內且重抽樣 gate 全數通過。
- 不得沿用的問題：不得在未產出 evidence 前宣稱策略具備重現性。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-supplemental-divergence--v003/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-supplemental-divergence--v003/candidate-definition.yml`
- Development evidence：無（允許路徑未找到）
- 程式／測試：`research/tsm-mean-reversion-supplemental-divergence--v003/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_supplemental_divergence_v003.py`、`tests/test_tsm_mean_reversion_supplemental_divergence_v003.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-supplemental-divergence--v004`：Study Development 成果卡

- Development 判定：`通過`
- Provenance（來源可信狀態）：`provenance-unknown`
- 前一個 Study：`tsm-mean-reversion-supplemental-divergence--v003`
- 記錄日期：`2026-09-08`

## 結論

> 在 2014–2018、base 每邊 1/5 bps 與 stress 每邊 2/20 bps 成本下，本 Study 的 Development 結果支持「均值回歸搭配量價背離補充路徑」的候選假說：完成交易 27 筆覆蓋五年，base 報酬 38.73%（PF 5.967）、stress 報酬 30.40%（PF 4.831），且最大回撤僅 2.00%，事前登記事前 gates 全數通過。

## 研究變更

- 研究問題或假說：TSM 低於 SMA(20) 1.5%、RSI(2)≤50 且成交量比率≥1.05 時，加入量價背離補充路徑是否能捕捉更優質的反彈時機。
- 相較上一個 Study 只改：完成並封存可核對之正式 Development evidence；策略進出場與風控規則維持同一設定。
- 保持不變或比較基準：10-session 持有、5-session cooldown、2% risk budget、-4%／+4% stop-target、base／stress 成本。

## 主要結果

| 條件 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 27 | 38.73% | 5.967 | 2.00% | 通過 |
| Development / stress | 27 | 30.40% | 4.831 | 2.00% | 通過 |

- 交易年度覆蓋：5（2014–2018）
- 失敗 gate：無；所有事前 Development gates（包含報酬、獲利因子、回撤、交易數與逐年剔除）全數通過。
- 未執行項目與原因：無；正式 evidence 完整。

## 主要發現

- 已確認：27 筆交易跨足五年（各年 2 至 7 筆），stress block bootstrap 正報酬比例為 100%、回撤超標比例為 0%，leave-one-year-out 逐年剔除後最低 stress 報酬仍有 19.73%、PF 3.792。
- 可能原因：低檔量價背離補充條件成功提供第二條有效過濾路徑，在未過度限制樣本的情況下提升了整體交易勝率與盈虧比；但背離條件與主路徑的邊際貢獻仍需進一步消融分析。
- 尚不能判斷：無獨立的 provenance declaration，來源可信狀態仍屬未確認；此外，背離各項參數（ATR 倍數、lookback 窗口）是否過度擬合尚無法從單一資料集得出定論。

## 下一輪

- 建議處置：建立有限 follow-up Study，對量價背離補充路徑進行單一參數敏感度測試或消融驗證。
- 下一個 Study 只測：單獨關閉或調整量價背離補充路徑中的觀察窗口（例如由 5 個 session 改為 3 個），其他參數不變。
- 成功／失敗條件：完成交易至少 20 筆，base/stress 報酬與 PF 維持通過，stress 回撤不超過 5%；任何 gate 失敗即否證該參數變更。
- 不得沿用的問題：不得在未做單一機制消融前，斷言量價背離為績效改善的唯一原因。

## 證據連結

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-supplemental-divergence--v004/manifests/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-supplemental-divergence--v004/candidate-definition.yml`
- Development evidence：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-supplemental-divergence--v004/evidence/development.yml`
- 程式／測試：`research/tsm-mean-reversion-supplemental-divergence--v004/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_supplemental_divergence_v004.py`、`tests/test_tsm_mean_reversion_supplemental_divergence_v004.py`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-selling-pressure-rollover--v001`：Study Development 成果卡

- 成果卡狀態：`evidence-unavailable`
- Development gate：`尚不能判斷`
- Provenance（來源可信狀態）：`verified-clean`
- candidate_freeze_status：`已完成`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v009`（Path A 明示來源）
- 記錄日期：`2026-09-09`

## 結論

> 本 Study 預先設定 2014–2018、base 每邊 1 bps 費用／5 bps 滑價、stress 每邊 2／20 bps，並要求至少 20 筆交易、3 個交易年度及正報酬與 PF 門檻。但必要的 Development evidence 不存在，因此無法判定新增「賣壓翻轉」Path B 是否改善成本後的均值回歸，也不能判定任何 gate 通過或失敗。

## 研究變更

- 研究問題或假說：TSM 超跌時，價格尚未反轉，但賣方成交量可能已先衰退。若三個 session 的 Signed Volume Balance（依漲跌方向加總成交量的賣壓指標）由前五個 session 的極負值回升，可能增加可接受的均值回歸交易。
- 相較上一個 Study 只改：保留 v009 的 Path A，新增不要求訊號日收盤上漲的 Path B；Path B 要求目前 SVB3 ≥ -0.15，且前五個 session 的最低值 ≤ -0.50。
- 保持不變或比較基準：SMA(20) 超跌 1.5%、RSI(2)≤50、下一個開盤進場、持有 10 個完整 session、5-session cooldown、2% risk budget、-4% stop／+4% target，以及簡單超跌 baseline。

## 主要結果

| 條件 | 狀態 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | gate／備註 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 證據不可用：`evidence/development.yml` 不存在 | — | — | — | — | 停止分析 |
| Development / stress | 證據不可用：`evidence/development.yml` 不存在 | — | — | — | — | 停止分析 |

- 交易年度覆蓋：證據不可用，無法確認。
- 失敗 gate：停止分析；沒有合法 evidence，不能判定通過或失敗。
- 未執行項目與原因：base／stress 指標、年度分段、bootstrap、逐年剔除與 gate 判定均無法核對；不得填零或推測。

## 主要發現

- 已確認：規格、Development inputs、runner、策略程式與測試路徑均存在；provenance declaration 為 `verified-clean`，並明確記載 candidate freeze 已完成。
- 可能原因：Development evidence 可能未產出或未發布；這只是低強度推論，現有資料無法確認實際原因。
- 尚不能判斷：交易數、報酬、PF、回撤、假說是否成立，以及任何 Development gate 狀態。
- 證據缺口與影響：缺少 `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-selling-pressure-rollover--v001/evidence/development.yml`，因此程式、測試與輸入檔不能代替實際結果證據。

## 下一輪

- 建議處置：修正 Development evidence 的產製與 validator 綁定流程，不調整策略參數。
- 下一個 Study 只測：以相同凍結候選補齊可驗證的 base／stress Development evidence。
- 成功／失敗條件：validator 接受合法 evidence，且兩種成本情境都含實際交易數、報酬、PF、回撤、年度與必要 diagnostics；否則仍為 `evidence-unavailable`。
- 不得沿用的問題：不得以程式存在、測試通過、輸入檔存在或 provenance 狀態推論策略結果。

## 允許讀取的 repository-relative 來源

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-selling-pressure-rollover--v001/manifests/preregistration.yml`
- Candidate definition：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-selling-pressure-rollover--v001/manifests/candidate-definition.yml`
- Development evidence：無；上述 `evidence/development.yml` 不存在
- 程式／測試：`research/tsm-mean-reversion-selling-pressure-rollover--v001/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_selling_pressure_rollover_v001.py`、`tests/test_tsm_mean_reversion_selling_pressure_rollover_v001.py`
- Provenance：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-selling-pressure-rollover--v001/evidence/provenance.yml`
- 詳細盲檢討：無

---

# `tsm-mean-reversion-selling-pressure-rollover--v002`：Study Development 成果卡

- 成果卡狀態：`complete`
- Development gate：`通過`
- Provenance（來源可信狀態）：`provenance-unknown`
- candidate_freeze_status：`未完成`
- 前一個 Study：`tsm-mean-reversion-selling-pressure-rollover--v001`
- 記錄日期：`2026-09-10`

## 結論

> 在 2014–2018 Development 期間、base 每邊 1／5 bps、stress 每邊 2／20 bps 下，本 Study 的 Development evidence 完整，正式 Development gates 全部通過，對「加入賣壓翻轉 Path B 可改善均值回歸」提供有限支持；但完成交易數與 stress return 未達事前 research targets，因此 candidate freeze 尚未完成。

## 研究變更

- 研究問題或假說：在 SMA(20) 超跌 1.5%、RSI(2)≤50 時，若前三日 SVB3 從前五日的極負值回升，是否能在不等待收盤上漲確認下增加有效交易。
- 主要變更：保留既有 v009 Path A，新增不要求訊號日上漲的 Path B。
- 保持不變：下一個 session open 進場、10-session 持有、5-session cooldown、2% risk budget、-4%／+4% stop-target 與相同成本模型。

## 主要結果

| 條件 | 狀態 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | gate／備註 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 已完成 | 26 | 37.52% | 5.391 | 2.00% | 正式 gates 通過 |
| Development / stress | 已完成 | 26 | 29.53% | 4.498 | 2.00% | 正式 gates 通過 |

- 交易年度覆蓋：5 年（2014–2018）。
- Research targets 失敗：完成交易 26 少於 30；stress return 29.53% 低於 30.40%。
- 未執行項目與原因：無。

## 主要發現

- 已確認：正式 Development gates 全部通過，且逐年剔除後 stress 結果仍維持正報酬。
- 可能原因：Path B 可能帶來額外機會，但目前只有 5 筆交易且全部獲利；同時它排擠了 3 筆既有 v009 交易，因此淨增量仍需更嚴格驗證。
- 尚不能判斷：Path B 在後續固定 Evaluation 中是否能維持優勢。
- 已確認的證據缺口、影響與限制：Provenance 尚無獨立聲明；realized drawdown 約 2.00%，但保守 mark-to-market stress drawdown 約 3.42%。

## 下一輪

- 建議處置：建立一個只測 Path B capacity／crowding 的 follow-up Study。
- 下一個 Study 只測：固定 Path A／Path B 優先順序，並扣除被排擠的既有交易後重新評估淨增量。
- 成功／失敗條件：完成交易至少 30 筆、stress return >30.40%，且 Path B 扣除被排擠交易後的淨增量仍為正。
- 不得沿用的問題：不得把 5 筆全正交易視為機制已被證明。

## 允許讀取的 repository-relative 來源

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-selling-pressure-rollover--v002/manifests/preregistration.yml`
- Candidate definition：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-selling-pressure-rollover--v002/manifests/candidate-definition.yml`
- Development evidence：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-selling-pressure-rollover--v002/evidence/development.yml`
- 程式／測試：`src/trading_2026_2/tsm_mean_reversion_selling_pressure_rollover_v001.py`、`tests/test_tsm_mean_reversion_selling_pressure_rollover_v001.py`
- 詳細盲檢討：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-selling-pressure-rollover--v002/reviews/001-first-review.md`
- 來源限制：本成果卡只整理 Development 階段，沒有讀取或引用正式 Historical Evaluation、Terminal 或 `historical-evaluation-artifacts/`。

---

# `tsm-mean-reversion-two-stage-volume-reversal--v013`：Study Development 成果卡

- 成果卡狀態：`complete`
- Development gate：`通過`
- Provenance（來源可信狀態）：`verified-clean`
- candidate_freeze_status：`未完成`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v009`
- 記錄日期：`2026-09-10`

## 結論

> 在 2014–2018 Development、base 每邊 1／5 bps、stress 每邊 2／20 bps 下，evidence 完整、formal gates 通過，成果卡為 `complete`；但提前解禁相對 v009 的改善假說不受本輪支持，candidate freeze 未完成。

## 研究變更

- 研究問題或假說：退場後放量事件若在三個 session 內獲得原有反轉條件確認，能否提前恢復交易。
- 唯一變更：加入提前冷卻重設；其餘訊號、執行、成本、風控與持有期沿用 v009。
- 比較基準：固定 v009 two-stage candidate。

## 主要結果

| 條件 | 狀態 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | gate／備註 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 已完成 | 25 | 24.399% | 3.353 | 2.362% | formal gates 通過 |
| Development / stress | 已完成 | 25 | 18.167% | 2.742 | 2.596% | formal gates 通過 |

- 交易年度覆蓋：5 年（2014–2018）；formal gates 無失敗，research targets 失敗 10 項，故 freeze 未完成。
- 未執行項目與原因：pytest 未執行，因環境缺少 pandas／pytest。

## 主要發現

- 已確認：新增 3 筆提前交易（2015–2016），base／stress PnL 為 -210.07／-677.31，並取代兩筆 v009 獲利交易；總交易數只增 1 筆，績效變差。
- 可能原因：放量 1.05 倍加一次收盤上漲，可能仍在同一下跌波段重入；這仍是推論。
- 尚不能判斷：正式 Historical Evaluation 的表現或失敗原因。
- 證據限制：evidence 可驗證，但 pytest 因環境缺 pandas／pytest 未執行。

## 下一輪

- 建議處置：停止本 Study freeze，建立有限 follow-up Study。
- 下一個 Study 只測：只禁止上一筆交易以 stop、stop-gap 或 stop-same-session 結束後啟動提前重設。
- 成功／失敗條件：formal gates 全通過，新增減被取代的 base／stress PnL >0，且 stress 報酬／PF／回撤不劣於 v009；任一失敗即停止。
- 不得沿用的問題：不得在原 Study 內事後改規則或把 formal gate 通過當成 freeze 通過。

## 允許讀取的 repository-relative 來源

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v013/manifests/preregistration.yml`
- Candidate definition：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v013/manifests/candidate-definition.yml`
- Development evidence：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v013/evidence/development.yml`
- Provenance：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v013/evidence/provenance.yml`
- 程式／測試：`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v013.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v013.py`
- 詳細盲檢討：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v013/reviews/001-blind-review.md`
- 來源限制：本成果卡只整理 Development 階段，沒有讀取或引用正式 Historical Evaluation、Terminal 或 `historical-evaluation-artifacts/`。

---

# `tsm-mean-reversion-two-stage-volume-reversal--v017`：Study Development 成果卡

- 成果卡狀態：`complete`
- Development gate：`通過`
- Provenance（來源可信狀態）：`provenance-unknown`
- candidate_freeze_status：`未完成`
- 前一個 Study：無（v017 規格未明示前版；Development 比較基準為 `tsm-mean-reversion-two-stage-volume-reversal--v009`）
- 記錄日期：`2026-09-11`

## 結論

> 在 2014–2018、base 每邊 1／5 bps、stress 每邊 2／20 bps、2% risk budget、10-session 持有與相同停損停利規則下，本成果卡狀態為 `complete`，formal Development gates 全部通過；但對「加入放量事件後的縮量淺回測，可在 v009 原有路徑之外增加成本後有優勢交易」的假說，本輪不支持。補充路徑實際接受 0 筆訊號，所有 24 筆交易都來自原有路徑，因此 candidate freeze 未完成。

## 研究變更

- 研究問題或假說：訊號日前第 2–5 個交易日若先有成交量至少為前 20 日均量 1.25 倍、收盤守住區間上半部的放量事件，之後出現不破事件低點的縮量收跌回測，是否能讓原本只需低於 SMA(20) 1.0%（含）至未滿 1.5% 的淺超跌訊號形成有效均值回歸機會。
- 相較比較基準只改：保留 v009 原有量先與收盤上漲路徑，新增一次性、最新事件優先的「放量→縮量回測→收盤反轉」補充路徑。
- 保持不變：下一個 XNYS session open 進場、10-session 持有、退場後 5-session cooldown、2% risk budget、-4%／+4% stop-target 與成本模型。

## 主要結果

| 條件 | 狀態 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | gate／備註 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 已完成 | 24 | 33.676% | 5.036 | 2.000% | formal gates 通過；freeze research targets 未全數通過 |
| Development / stress | 已完成 | 24 | 26.523% | 4.204 | 2.119% | formal gates 通過；stress 30.40% 目標失敗 |

- 交易年度覆蓋：5 年（2014–2018）。
- 失敗 gate：無 formal Development gate 失敗；但 research targets 有 7 項失敗，包括完成交易 24<30、相對 v009 未增加交易（24 不大於 24）、新增交易數 0<1、新增交易年度 0<3、兩套成本下淨新增減被排擠損益均為 0，以及 stress 報酬 26.523%<30.40%。
- 未執行項目與原因：無；交易區塊 bootstrap、calendar block bootstrap 與 leave-one-signal-year-out 均有 evidence。

## 主要發現

- 已確認：`evidence/development.yml` 通過 Development validator；base／stress 報酬與 PF 均為正，stress block bootstrap 正報酬比例最低為 99.998%，逐年剔除後最低 stress 報酬 18.030%、PF 3.409，formal gates 全數通過。
- 已確認：補充路徑建立 164 個放量事件，但接受的補充確認與補充交易都是 0；v017 與 v009 的交易數、報酬、PF、回撤完全一致，顯示本輪沒有量到新增機制的邊際效果。
- 可能原因：嚴格的 2–5 session 事件窗口、低點不可跌破與單次消耗規則，可能讓事件在完成回測與訊號確認前過期、失效或被新事件取代；evidence 只支持這個可能性，不能分辨主因。
- 尚不能判斷：不能由本輪結果判斷補充路徑在較寬時間窗口下是否有效，也不能把原有路徑的正報酬歸因於新增路徑。
- 已確認的證據缺口、影響與限制：允許讀取資料沒有獨立 provenance declaration，故來源可信狀態仍為 `provenance-unknown`；24 筆交易也低於 freeze 所要求的 30 筆，正報酬不能抵銷上述新增交易目標失敗。

## 下一輪

- 建議處置：停止 v017 candidate freeze，不在原 Study 內調參或重跑。
- 下一個 Study 只測：若仍要延伸，只把補充事件的有效觀察窗口（含 expiry）由 5 個 session 延長至 7 個 session；其餘訊號、成本、執行與風控固定。
- 成功／失敗條件：formal Development gates 全部通過，且補充路徑至少產生 1 筆交易、分布於至少 3 個 signal years、總交易至少 30 筆、stress 報酬至少 30.40%，兩套成本下淨新增減被排擠損益都嚴格大於 0；任一條件失敗即停止。
- 不得沿用的問題：不得用本輪與 v009 完全相同的 aggregate metrics 宣稱縮量淺回測機制已被驗證，也不得把 0 筆新增交易當成可估計的增量效果。

## 允許讀取的 repository-relative 來源

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v017/manifests/preregistration.yml`
- Candidate definition：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v017/manifests/candidate-definition.yml`
- Development evidence：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v017/evidence/development.yml`
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v017/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v017.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v017.py`、`research/tools/development_status.py`
- 詳細盲檢討：無
- 來源限制：本成果卡只整理 Development 階段，沒有讀取或引用正式 Historical Evaluation、Terminal 或 `historical-evaluation-artifacts/`。

---

# `tsm-mean-reversion-two-stage-volume-reversal--v014`：Study Development 成果卡

- 成果卡狀態：`evidence-unavailable`
- Development gate：`尚不能判斷`
- Provenance（來源可信狀態）：`未確認`
- candidate_freeze_status：`尚不能判斷`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v013`
- 記錄日期：`2026-09-11`

## 結論

> 在事前規格的 2014–2018、base 每邊 1／5 bps、stress 每邊 2／20 bps 成本下，本成果卡狀態為 `evidence-unavailable`。v014 的規格與程式路徑可以確認，但找不到可驗證的 `evidence/development.yml`，因此不能判定 base／stress 的交易、報酬、PF、回撤、Development gate 或 candidate freeze，也不能以程式與輸入檔代替結果證據。

## 研究變更

- 研究問題或假說：訊號日前第 2–5 個交易日若先有成交量至少為前 20 日均量 1.25 倍的放量事件，之後出現收跌、量縮至事件量 80% 以下且不跌破事件低點的淺回測，是否能在原本 1.5% 超跌門檻之外，形成扣除成本後有優勢的均值回歸機會。
- 相較上一個 Study 只改：移除 v013 的退場冷卻提前重設，改加入獨立的「放量事件→縮量回測→訊號日收盤上漲」補充路徑；它與 v009 原有路徑並存，原路徑優先。
- 保持不變或比較基準：v009 的資料、進場與退場、2% 風險預算、10 個完整持有 session、停損停利、冷卻與成本口徑。

## 主要結果

| 條件 | 狀態 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | gate／備註 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 證據不可用：缺少 `evidence/development.yml` |  |  |  |  | 停止分析 |
| Development / stress | 證據不可用：缺少 `evidence/development.yml` |  |  |  |  | 停止分析 |

- 交易年度覆蓋：證據不可用：沒有合法 Development evidence。
- 失敗 gate：停止分析：缺少可被 validator 驗證的 `evidence/development.yml`，不判定 gate 失敗或通過。
- 未執行項目與原因：尚不能判斷；目前無法區分 Development 未執行、證據未保存或路徑未對齊。

## 主要發現

- 已確認：v014 的 preregistration 與 implementation contract 已固定補充路徑、成本、執行與比較 v009 的規格；但允許讀取範圍內沒有候選結果 evidence。
- 可能原因：結果檔可能尚未產製、未封存，或產出路徑與 workflow 期待不一致；這只是流程層面的可能解釋，沒有證據支持其中任何一項。
- 尚不能判斷：補充路徑是否產生交易、base／stress 是否通過門檻、研究目標是否達成，以及 candidate 是否可 freeze。
- 已確認的證據缺口、影響與限制：缺少 `evidence/development.yml` 使所有數值與 gate 分析停止；不得用 runner、程式或 input 重建數值。

## 下一輪

- 建議處置：修正 Development evidence 的產製、驗證與封存流程；不要在 v014 內補跑或調整策略參數。
- 下一個 Study 只測：只驗證同一候選能否產出一份被 validator 接受、同時包含 base／stress 與 status table 的 `evidence/development.yml`。
- 成功／失敗條件：檔案存在、validator 接受、base／stress 結果完整且 status 與 gates／research targets 一致即成功；缺檔、無法驗證或任一情境缺資料即失敗。
- 不得沿用的問題：不得把規格存在、測試通過或 runner 可執行解讀成策略結果，也不得在證據缺失時宣稱假說有效或失敗。

## 允許讀取的 repository-relative 來源

- Preregistration：`research/tsm-mean-reversion-two-stage-volume-reversal--v014/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v014/candidate-definition.yml`
- Development evidence：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v014/evidence/development.yml`（缺失）
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v014/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v014.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v014.py`
- 詳細盲檢討：無
- 來源限制：本成果卡只整理 Development 階段，沒有讀取或引用正式 Historical Evaluation、Terminal 或 `historical-evaluation-artifacts/`。

---

# `tsm-mean-reversion-two-stage-volume-reversal--v015`：Study Development 成果卡

- 成果卡狀態：`evidence-unavailable`
- Development gate：`尚不能判斷`
- Provenance（來源可信狀態）：`未確認`
- candidate_freeze_status：`尚不能判斷`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v014`
- 記錄日期：`2026-09-11`

## 結論

> 在同一套 2014–2018、base 每邊 1／5 bps、stress 每邊 2／20 bps 成本規格下，本成果卡狀態為 `evidence-unavailable`。v015 的 workflow 與 research 目錄目前只有 Development authorization，沒有可被驗證的 `evidence/development.yml`；因此不能判定任何 base／stress 結果、Development gate、研究目標或 candidate freeze，也不能把 v014 的結果假設沿用到 v015。

## 研究變更

- 研究問題或假說：延續 v014 的放量後縮量淺回測補充路徑，檢驗訊號日只需低於 SMA(20) 1.0%（含）但未達 1.5% 時，是否能形成成本後有優勢的均值回歸交易。
- 相較上一個 Study 只改：明確綁定 v009 Study-local comparison control，並將同一套候選與 Development runner／證據路徑版本化；v014 與 v015 的策略 source diff 為空，因此沒有可確認的策略規則變更。
- 保持不變或比較基準：補充路徑條件、v009 原有路徑、資料期間、成本、2% 風險預算、10-session 持有、停損停利與冷卻規則。

## 主要結果

| 條件 | 狀態 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | gate／備註 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 證據不可用：沒有 `evidence/development.yml`；目前僅有 authorization |  |  |  |  | 停止分析 |
| Development / stress | 證據不可用：沒有 `evidence/development.yml`；目前僅有 authorization |  |  |  |  | 停止分析 |

- 交易年度覆蓋：證據不可用：沒有合法 Development evidence。
- 失敗 gate：停止分析：缺少可被 validator 驗證的 `evidence/development.yml`，不判定 gate 失敗或通過。
- 未執行項目與原因：尚不能判斷；authorization 只能確認 Development scope，不能證明結果已產出或完整。

## 主要發現

- 已確認：v015 preregistration 已固定 v009 comparison control 與同一個補充路徑假說；策略 source 與 v014 相同，版本差異主要在 Study／runner／比較控制封裝。
- 可能原因：證據可能尚未產製、未封存，或只保留 authorization 而未完成結果發布；目前資料不能在這些解釋之間做選擇。
- 尚不能判斷：v015 是否實際執行 base／stress、補充路徑是否新增交易、任何報酬或回撤，以及 candidate 是否可 freeze。
- 已確認的證據缺口、影響與限制：workflow 與 research 的 evidence 目錄都沒有 `development.yml`；因此不能用 v014、v009 或程式輸出補足 v015 結果。

## 下一輪

- 建議處置：修正 Development evidence 產製、validator 驗證與封存鏈；保持策略規則不變，不在 v015 內重跑或調參。
- 下一個 Study 只測：只驗證候選結果能否產出並封存一份與 v009 control 綁定、可被 validator 接受的 `evidence/development.yml`。
- 成功／失敗條件：evidence 存在且合法、base／stress 完整、status table 與 gates／research targets 一致即成功；任一缺失或不一致即失敗。
- 不得沿用的問題：不得把 authorization、source diff 為空或程式可執行當成 Development outcome，也不得在證據缺失時宣稱機制有效。

## 允許讀取的 repository-relative 來源

- Preregistration：`research/tsm-mean-reversion-two-stage-volume-reversal--v015/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v015/candidate-definition.yml`
- Development evidence：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v015/evidence/development.yml`（缺失；目前僅有 `development-authorization.yml`）
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v015/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v015.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v015.py`
- 詳細盲檢討：無
- 來源限制：本成果卡只整理 Development 階段，沒有讀取或引用正式 Historical Evaluation、Terminal 或 `historical-evaluation-artifacts/`。

---

# `tsm-mean-reversion-two-stage-volume-reversal--v016`：Study Development 成果卡

- 成果卡狀態：`complete`
- Development gate：`通過`
- Provenance（來源可信狀態）：`provenance-unknown`
- candidate_freeze_status：`未完成`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v015`
- 記錄日期：`2026-09-11`

## 結論

> 在 2014–2018、base 每邊 1／5 bps、stress 每邊 2／20 bps、2% risk budget、10 個完整持有 session 與既定停損停利規則下，`evidence/development.yml` 已通過 validator，且 formal Development gates 全部通過；本成果卡狀態為 `complete`。但 7 項預先登記 research targets 失敗：v016 只有 24 筆、沒有補充路徑新增交易，stress 報酬為 26.523% 未達 30.40%，所以 candidate freeze 未完成，不能把補充機制視為已被支持。

## 研究變更

- 研究問題或假說：放量事件後的縮量、不破低點淺回測，是否能在原 v009 路徑外增加扣除成本後有優勢的均值回歸機會；補充路徑只在訊號日前 2–5 個交易日有效，且與原路徑並存但不增加持倉。
- 相較上一個 Study 只改：策略 source 與 v015 相同；v016 主要是同一候選的版本化 Study／runner 與獨立 Development evidence，沒有新的策略參數變更。
- 保持不變或比較基準：v009 原有路徑、資料與 2014–2018 期間、base／stress 成本、2% 風險預算、10-session 持有、5-session 冷卻、停損停利與進出場口徑。

## 主要結果

| 條件 | 狀態 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | gate／備註 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 已完成 | 24 | 33.676% | 5.036 | 2.000% | formal gates 通過；研究目標未全數通過 |
| Development / stress | 已完成 | 24 | 26.523% | 4.204 | 2.119% | formal gates 通過；30.40% 研究目標失敗 |

- 交易年度覆蓋：5 年（2014–2018）。
- 失敗 gate：無 formal Development gate 失敗；research targets 失敗包括完成交易至少 30、交易數多於 v009、新增交易至少 1 筆且分布至少 3 年、base／stress 淨新增減被排擠損益嚴格大於 0，以及 stress 報酬至少 30.40%。實際新增交易為 0、兩套成本下淨新增損益為 0。
- 未執行項目與原因：無；交易區塊 bootstrap 與 leave-one-signal-year-out evidence 已存在並通過正式 Development gate，calendar block bootstrap 為描述性診斷。

## 主要發現

- 已確認：validator 接受 evidence；base／stress 報酬、PF 均為正，最大回撤分別為 2.000% 與 2.119%，formal gates 全數通過。
- 已確認：建立 164 個放量事件，但補充確認與補充交易均為 0；24 筆交易全部來自 original path，v016 combined 與 v009 original path 的交易數、報酬、PF、回撤完全一致。因此本輪沒有量到補充機制的邊際效果。
- 可能原因：2–5 session 事件窗口、5-session expiry，以及事件被 invalidated／replaced 的規則可能過於嚴格；evidence 只支持這個可能性，不能分辨哪一項是主因。
- 尚不能判斷：若放寬有效窗口，補充路徑是否會產生可重現且不排擠原路徑的增量效果；也不能把原有路徑的正報酬歸因於補充機制。
- 已確認的證據缺口、影響與限制：沒有獨立 provenance declaration，來源可信狀態仍為 `provenance-unknown`；新增交易為 0，使增量效果無法估計，且研究目標失敗阻止 candidate freeze。

## 下一輪

- 建議處置：停止 v016 candidate freeze；若要延伸，建立有限 follow-up Study，不在原 Study 內調參或重跑。
- 下一個 Study 只測：只把補充事件的有效觀察窗口／expiry 從 5 個 session 延長到 7 個 session，其餘訊號、成本、執行與風控固定。
- 成功／失敗條件：formal Development gates 全通過，補充路徑至少新增 1 筆交易且分布於至少 3 個 signal years，總交易至少 30 筆，stress 報酬至少 30.40%，兩套成本下淨新增減被排擠損益都嚴格大於 0；任一條件失敗即停止。
- 不得沿用的問題：不得用與 v009 完全相同的 aggregate metrics 宣稱補充機制已驗證，也不得把 0 筆新增交易當成可估計的增量效果。

## 允許讀取的 repository-relative 來源

- Preregistration：`research/tsm-mean-reversion-two-stage-volume-reversal--v016/preregistration.yml`
- Candidate definition：`research/tsm-mean-reversion-two-stage-volume-reversal--v016/candidate-definition.yml`
- Development evidence：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v016/evidence/development.yml`
- 程式／測試：`research/tsm-mean-reversion-two-stage-volume-reversal--v016/run_development.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v016.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v016.py`、`research/tools/development_status.py`
- 詳細盲檢討：無
- 來源限制：本成果卡只整理 Development 階段，沒有讀取或引用正式 Historical Evaluation、Terminal 或 `historical-evaluation-artifacts/`。

---

# `tsm-mean-reversion-two-stage-volume-reversal--v018`：Study Development 成果卡

- 成果卡狀態：`complete`
- Development gate：`通過`
- Provenance（來源可信狀態）：`verified-clean`
- candidate_freeze_status：`未完成`
- 前一個 Study：`tsm-mean-reversion-two-stage-volume-reversal--v017`
- 記錄日期：`2026-09-11`

## 結論

> 在 2014–2018、base 每邊 1／5 bps、stress 每邊 2／20 bps、2% risk budget、4% stop／target 與 10-session 持有下，本成果卡狀態為 `complete`，且 formal Development gates 全部通過；但 v018 想驗證的淺回落補充路徑沒有產生任何 raw signal 或交易。24 筆交易全部來自 v009 原有路徑，因此本次無法支持 v018 的增量假說，candidate freeze 未完成。

## 研究變更

- 研究問題或假說：連續兩日放量、跌幅收斂、低點守住，若訊號日只比 SMA(20) 低 1.0% 至未滿 1.5% 且收盤轉強，是否能增加成本後有優勢的均值回歸交易。
- 相較上一個 Study 只改：在 v009 原有訊號路徑上加入事前固定的淺回落補充路徑；原路徑、成本、風險、停損停利、持有期與冷卻規則維持不變。
- 保持不變或比較基準：v009 comparison control、2013 warmup／2014–2018 Development、下一個 XNYS open 進場與單一部位執行口徑。

## 主要結果

| 條件 | 狀態 | 完成交易 | 報酬 | PF（Profit Factor，獲利因子） | 最大回撤 | gate／備註 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Development / base | 已完成 | 24 | 33.676% | 5.036 | 2.000% | formal gate 通過；research targets 未全數通過 |
| Development / stress | 已完成 | 24 | 26.523% | 4.204 | 2.119% | formal gate 通過；research targets 未全數通過 |

- 交易年度覆蓋：5 年（2014–2018）。
- 失敗 gate：無 formal Development gate 失敗；research targets 失敗包括交易至少 30 筆、交易數多於 v009、新增交易至少 1 筆且分布至少 3 年，以及 base／stress 淨新增減被排擠損益大於 0。實際新增交易與淨新增損益均為 0。
- 未執行項目與原因：無；bootstrap、leave-one-signal-year-out 與成本壓力結果均已產出。限制是補充路徑本身沒有觀測值。

## 主要發現

- 已確認：Development evidence 已被 validator 接受，base／stress 結果完整，formal gates 通過；補充路徑 raw signal、accepted signal 與 completed trade 均為 0，v018 combined 的 24 筆交易與 v009 原路徑相同。
- 可能原因：補充路徑把兩日成交量、跌幅收斂、低點守住、淺 gap、RSI 與收盤轉強全部串成必要條件，交集可能過窄；也可能被單一部位與 cooldown 擋下，但現有 evidence 不能分辨主因。
- 尚不能判斷：補充機制在其他資料期間是否有效，也不能把既有 v009 交易的正報酬歸因於 v018。
- 已確認的證據缺口、影響與限制：Development 只有 24 筆交易，且全數是原路徑；因此本卡能判定 gate 與既有路徑表現，不能估計 v018 的增量效果。

## 下一輪

- 建議處置：停止 v018 candidate freeze，不在原 Study 內調參或重跑。
- 下一個 Study 只測：另建一個 follow-up，只放寬一項事前有機制理由的補充條件；原 v009 路徑、成本、執行、風控與比較控制全部固定。
- 成功／失敗條件：formal Development gates 全部通過，補充路徑至少有 1 筆新增交易且分布於至少 3 個 signal years，總交易至少 30 筆，base／stress 淨新增減被排擠損益均嚴格大於 0；任一條件失敗即停止。
- 不得沿用的問題：不得用本輪 v009 原路徑的 24 筆交易宣稱 v018 補充機制已被驗證，也不得依本輪結果在原 Study 事後挑參數。

## 允許讀取的 repository-relative 來源

- Preregistration：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/manifests/preregistration.yml`
- Candidate definition：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/manifests/candidate-definition.yml`
- Development evidence：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/evidence/development.yml`
- Provenance：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/evidence/provenance.yml`
- 程式／測試：`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v018.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v018.py`、`research/tools/development_status.py`
- 詳細盲檢討：`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/reviews/001-first-review.md`
- 來源限制：本成果卡只整理 Development 階段，沒有讀取或引用正式 Historical Evaluation、Terminal 或 `historical-evaluation-artifacts/`。
