# tsm-mean-reversion-two-stage-volume-reversal--v006 封存式 blind review 001

## 1. 範圍與結論限制

- workflow：`strategy-forward-replication-research--v001`
- Study：`tsm-mean-reversion-two-stage-volume-reversal--v006`
- 角色：study 開發者
- Development warmup：2013-01-01 至 2013-12-31
- Development signal／交易期間：2014-01-01 至 2018-12-31
- 本次只使用研究設計、候選規格、策略程式、測試與 Development evidence。

結論先說：Development evidence 的既有 gate 全部通過，且在這段 Development 資料內，候選的結果相當穩定；但目前仍有一個優先級最高的規格／實作缺口：`maximum_drawdown` 實際上只用已完成交易的 PnL 計算，沒有明確定義是否要納入持倉內的未實現波動。這會讓「最大回撤」這個風險 gate 可能低估持倉期間的實際資金壓力。

本報告沒有讀取或使用目標 Study 的正式 Historical Evaluation 或 Terminal 結果，也不回答正式結果為何成功或失敗。

## 2. 實際問題與影響

### 2.1 最高優先：最大回撤的定義與實作不完全對齊

`qualification_metrics()` 只在每筆交易完成後把 `trade.pnl` 加到資金曲線，再從這條「交易結束點」資金曲線計算最大回撤（`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v006.py:422-445`）。Development gate 使用的名稱則是 `stress_maximum_drawdown`，沒有寫明它是「已實現交易回撤」或「持倉內 mark-to-market 回撤」（`manifests/preregistration.yml:123-131`）。

實際影響是：若部位在一個 session 內先大幅不利、之後又沒有觸發 stop 而回升，這段資金壓力不會進入目前的最大回撤；它只會在交易結束時以最終 PnL 出現。這不是已證明的 Evaluation 問題，但會讓風險 gate 的語意不夠明確，應在下一輪凍結前先修正。

### 2.2 Development 樣本很小，而且損失路徑異常平滑

候選只有 20 筆完成交易，雖然分布在 5 個 signal year，但 2017 年只有 2 筆（`evidence/development.yml:122-142`）。我從 20 筆交易紀錄重算：

- base：17 勝 3 負，return 28.10%，profit factor 6.12。
- stress：15 勝 5 負，return 22.31%，profit factor 5.00。
- stress 最長連敗為 1 筆；5 筆虧損交易都沒有形成連續虧損。
- stress exit reason 為 6 筆 `target-gap`、6 筆 `target`、6 筆 `time`、2 筆 `stop`。

這表示目前的回撤主要被「單筆 stop 約 2% 風險」與沒有連續虧損的交易順序限制住。它不代表結果錯誤，但對連續不利環境的證據很少。現有 block bootstrap 是從這 20 筆交易的連續區塊重抽，不是從更多市場日期或不同市場狀態建立獨立樣本。

### 2.3 「量先＋價行」的機制尚未被拆開驗證

候選同時要求：20 日均線負偏離至少 1.5%、RSI(2) 不高於 50、前 5 個 session 內曾有成交量異常，以及訊號日收盤高於前一日（`manifests/preregistration.yml:10-32`）。其中 SMA gap、RSI(2) 與訊號日漲跌都由同一組收盤價衍生；成交量條件又只取 5 日內最大比率。因此看起來像多重確認，但不一定代表多個獨立資訊來源。

目前 Development 只有「完整候選」與移除量先／價行兩個條件的 baseline 比較，沒有在本 Study 內拆出量先單獨、價行單獨的增量效果。候選比 baseline 少很多交易（20 對 44），所以較高的總報酬可以支持「篩選後的交易集合較好」，但不能單獨證明兩個條件各自都在避免接刀。

## 3. 規格與實作檢查

### 已確認大致一致的部分

從候選規格、程式與測試交叉核對，以下部分沒有發現明確的時間穿越或規則不一致：

- 訊號在 completed-session close 判定；SMA、RSI 使用當日及更早收盤價，成交量條件使用訊號日前的 5 個 session（`src/...v006.py:158-192`）。
- 進場在下一個 session open；gap、同日 stop／target 及 stop-first 規則有實作（`src/...v006.py:237-254`）。
- 部位最多一筆、不借款，股數同時受可用現金與含成本的 stop 風險預算限制（`src/...v006.py:204-234`）。
- time exit、持倉互斥、退出後 5 個 completed session 的 cooldown 與 fold warmup 都有對應程式與測試（`src/...v006.py:301-417`；`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v006.py:126-179`）。

### 規格／實作缺口

1. **最大回撤的語意未凍結。** 程式明確採用已完成交易 PnL，但規格只寫 `maximum_drawdown`；應明確改名為 realized drawdown，或補上持倉內估值的計算規則與測試。
2. **RSI 的計算方法沒有寫進 preregistration。** 程式使用簡單 rolling mean 的 gain／loss（`src/...v006.py:133-155`），而規格只寫 `RSI(2)`。若日後有人使用 Wilder RSI，同一個 `RSI(2)` 會產生不同訊號；這是可重現性缺口，不是本次已證明的策略錯誤。
3. **候選 family 識別字串不一致。** `baseline_definition.candidate_family` 使用 `tsm-mean-reversion-two-stage-time-decay-v006`，但 `complete_candidate_family`、`selected_candidate_id` 與 Development evidence 使用 `tsm-mr-two-stage-time-decay-v006`（`manifests/preregistration.yml:1-9, 203-207`；`evidence/development.yml:31,44`）。這可能只是名稱欄位與 ID 欄位混用，但應在下一輪統一，避免治理檔案與 evidence 綁定到不同名稱。

### 測試覆蓋的限制

測試已覆蓋 prior-only 成交量、next-open、gap fill、stop-first、risk budget、cooldown 與 fold warmup；但沒有看到針對以下規則的直接測試：

- 持倉內未實現波動是否計入最大回撤；
- `signal_end` 附近的完整交易生命週期截斷；
- time exit 到期當日，時間退出和同日 stop／target 的優先順序。

這些是下一輪應補的驗收測試，不把它們直接當成本 Study 已發生的程式錯誤。

## 4. Development 穩健度

### 已重算與 evidence 相符的指標

`evidence/development.yml` 顯示候選的 Development gate 全部通過（`evidence/development.yml:207-308`）：

| 指標 | base | stress |
| --- | ---: | ---: |
| 完成交易數 | 20 | 20 |
| traded years | 5 | 5 |
| return | 28.10% | 22.31% |
| profit factor | 6.12 | 5.00 |
| 最大回撤（目前實作的已實現交易資金曲線） | 2.00% | 2.12% |
| 最大單筆實現虧損 | 約 2.00% | 約 2.00% |

與 baseline 相比，候選 stress return 為 22.31%，baseline 為 1.80%；但候選只有 20 筆交易，baseline 有 44 筆，這項差異應解讀為交易篩選結果的比較，不是獨立證明某一個條件的因果效果（`evidence/development.yml:2-35`）。

### 分年與不確定性

- signal year 交易數為 2014／2015／2016／2017／2018 的 5／5／4／2／4 筆；stress PnL 分別約為 5.21%、6.78%、0.75%、0.87%、8.70% 的初始現金比例。
- stress leave-one-year-out 仍全部為正，最低 return 為 13.61%，最低 profit factor 為 3.44（`evidence/development.yml:176-206`）。這表示本段 Development 結論不依賴單一年度，但不能補足每年交易數很少的問題。
- 50,000 次 block bootstrap 的 stress 結果，block length 3／5 的正報酬比例為 99.978%／99.84%，stress return 的 5th percentile 約為 10.70%／9.64%，profit factor 的 5th percentile 約為 2.15／1.99；最大回撤超過 10% 的比例為 0（`evidence/development.yml:85-121`）。這支持「在這 20 筆交易的重抽樣下結果穩定」，但不等於已驗證新的市場日期或新的 regime。

## 5. 調整優先順序

### 第一優先：規格／實作缺口

**調整：** 凍結最大回撤的定義，並讓欄位名稱、gate 與計算一致；同時新增一個持倉中出現大幅不利但未觸發 stop 的測試案例。若決定使用 mark-to-market，需預先寫明日線 OHLC 下的估值與同日歧義處理；若決定只看已實現資金曲線，欄位應明確標成 realized drawdown。

**驗收：** 規格、evidence 欄位、程式與測試對同一個回撤定義逐字一致，並能在人工構造的未實現回撤案例中得到預期結果。

### 第二優先：Development 警訊

**調整：** 下一個 Study 預先登記一個尊重日期連續性的風險診斷，讓連續不利 session／交易群聚能影響結果，而不是只重抽目前 20 筆交易；同時保留現有 leave-one-year-out 作為補充。

**預期解決的問題：** 檢查「沒有連續虧損」是否只是目前樣本的交易順序，而不是風險路徑的可靠特徵。

**驗收：** 新 Study 事前固定 block 定義、種子、重抽次數與 gate；不得在看到新結果後調整 block 長度或門檻。

### 第三優先：未驗證設計假說

**調整：** 在新 Study 中預先登記量先單獨、價行單獨與完整候選的有限 ablation，並使用相同成本、部位與暴露規則比較。另應明確寫出 RSI 的公式，以及「5 日內任一量能尖峰」是否真的代表相同的資訊。

**預期解決的問題：** 分辨完整候選的優勢來自量能條件、價格反轉條件，還是只是更少交易後留下的特定樣本。

**驗收：** 只接受事前指定的少數比較；任一新想法都建立新 Study，不回寫本 Study 的結果或 digest。

## 6. 不能得出的結論

本次 review 不能判斷正式 Historical Evaluation 是否通過、是否失敗，也不能指出正式結果的失敗原因。以上設計風險與 Development 警訊都不能被寫成正式 Evaluation 的事後解釋；建議也不保證下一輪一定改善結果。

## 7. 讀取紀錄

本次實際讀取：

- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v006/manifests/preregistration.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v006/manifests/candidate-definition.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v006/manifests/qualification-spec.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v006/manifests/development-trial-inputs.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v006/manifests/source-bundle.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v006/manifests/data-snapshot-acquisition.yml`（只讀取來源、日期、完整性與角色 metadata）
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v006/evidence/development.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v006/evidence/development-authorization.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v006/evidence/provenance.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v006/evidence/selection-evidence.yml`
- `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v006.py`
- `tests/test_tsm_mean_reversion_two_stage_volume_reversal_v006.py`
- `pyproject.toml`
- `.agents/skills/blind-review-strategy-study/SKILL.md`
- `.agents/skills/blind-review-strategy-study/references/review-method.md`

本次沒有讀取或使用 `study.yml`、正式 Historical Evaluation／Terminal evidence、Evaluation／replay payload、quarantine 或 full 原始價格快照、`README.md`、`events/000008-*` 之後事件、`journals/`，也沒有使用網路、外部市場資料、broker 或 connector。
