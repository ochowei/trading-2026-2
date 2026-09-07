# Study 封存式盲檢討報告：tsm-mean-reversion-two-stage-volume-reversal--v009

## 1. 範圍與結論限制

- **檢討角色**：study 開發者
- **目標 Workflow**：`strategy-forward-replication-research--v001`
- **目標 Study ID**：`tsm-mean-reversion-two-stage-volume-reversal--v009`
- **檢討性質**：封存式盲檢討（Blind Review）。
- **資料範圍**：僅使用已獲授權的暖機期間（Warmup：2013-01-01 至 2013-12-31）與開發期間（Development：2014-01-01 至 2018-12-31）資料、規格清單與策略原始碼。
- **邊界聲明**：本次檢討完全未讀取、未引用、亦未推測任何正式歷史評估（Historical Evaluation）或終止結果（Terminal Evidence）。本報告不評估策略在 2020–2024 年正式評估期的表現，亦不保證後續修改能通過正式評估。

---

## 2. 實際問題與影響（白話核心摘要）

在台積電（TSM）短線均值回歸策略的設計中，主要預期在股價跌破 20 日均線（SMA20）1.5% 且 2 日強弱指標（RSI）偏低時，藉由「過去 5 日曾出現成交量放大（均量 1.05 倍）」作為換手支撐訊號，並在隔天收盤高於前一天時進場做多。

本次檢討發現以下三大核心問題：

1. **成交量濾網看似神奇，實為對單一虧損交易的「精準過度配適」**：
   - **實際情況**：在 2014 至 2018 年整整 5 年中，啟用成交量濾網與「完全不用成交量濾網（純看價格）」相比，整整 5 年的交易訊號中**僅僅只差了 1 筆交易**（2018 年 4 月 9 日）。
   - **造成的影響**：被剔除的這唯一一筆交易，剛好在隔週發生了「跳空下跌停損」（單筆虧損約 2.5%）。因為碰巧避開了這筆虧損，策略帳面獲利因子（Profit Factor）從 3.86 暴增到 5.04。然而，門檻設為 1.05 倍（僅比 20 日平均成交量高出 5%），在日常交易中根本就是常態波動（通過率高達 96%）。一旦市場環境或雜訊微調（例如在參數擾動測試中將門檻設為 1.00 倍），該筆虧損立刻重新出現，優異績效被打回原形。這表示策略假說所稱的「成交量領先可有效辨識假止跌」，在統計上缺乏堅實基礎，實質上只是碰巧排除了一個歷史特例。

2. **開發紀錄檔存在嚴重標籤顛倒缺陷**：
   - **實際情況**：在開發證據檔（`evidence/development.yml`）中的「機制消融分析」（Mechanism Ablation）區塊，候選策略（`calibrated_two_stage`）與純價格對照組（`price_only`）的數據標籤被顛倒填入。
   - **造成的影響**：報告文件顯示候選組只有 25 筆交易、獲利因子 3.86，而純價格組卻有 24 筆交易、獲利因子 5.04；但程式實際運算結果恰恰相反。這造成證據檔內部與頂層候選數據（24 筆、獲利因子 5.04）相互矛盾，會嚴重誤導審查者與後續開發者對各項機制效果的判斷。

3. **有效樣本數逼近失格邊緣，且年度分佈極端不均**：
   - **實際情況**：5 年期間總共僅累積 24 筆交易，距離流程規範的最低門檻（20 筆）僅有 4 筆緩衝。尤其在 2017 年台積電強勁牛市期間，整年竟然只觸發了 2 筆交易。
   - **造成的影響**：策略進場條件極為嚴格且高度仰賴拉回回調。若後續年度持續呈現強勢單邊行情或波動縮小，交易次數極易跌破 20 筆的合格門檻而直接遭系統否證淘汰。

---

## 3. 規格與實作檢查

經對照預先登記文件（`preregistration.yml`）、候選定義（`candidate-definition.yml`）與實際程式碼（`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py`）：

### 3.1 已確認的實作與紀錄缺陷
- **證據檔機制消融標籤反轉（Defect）**：
  - 在 `evidence/development.yml` 第 275–305 行的 `mechanism_ablation` 中：
    - `calibrated_two_stage`（本應對應 `DEFAULT_SPEC`，包含成交量條件）：紀錄為 25 筆交易、報酬率 30.97%、獲利因子 3.86。
    - `price_only`（本應對應 `PRICE_ONLY_SPEC`，關閉成交量條件）：紀錄為 24 筆交易、報酬率 33.68%、獲利因子 5.04。
  - **程式驗證**：以相同資料重新執行 `DEFAULT_SPEC`，產生 24 筆交易、報酬率 33.68%、獲利因子 5.04；執行 `PRICE_ONLY_SPEC` 則產生 25 筆交易、報酬率 30.97%、獲利因子 3.86。
  - **結論**：此處確認為開發紀錄輸出時字典鍵值（keys）對調所產生的文件缺陷。

### 3.2 規格與程式一致性（無偷看與時序漏洞）
- **決策與進場時間點**：訊號於當日收盤確認（`completed-session-close`），進場以次一交易日開盤價（`next-session-open-market`）模擬，無未來資訊外洩（No Lookahead）。
- **成交與成本模型**：
  - 一般情境（Base）：單邊手續費 1 bps、滑價 5 bps。
  - 壓力情境（Stress）：單邊手續費 2 bps、滑價 20 bps。
  - 盤中跳空優先處理（`intraday_ambiguity`）：跳空開在停損價下方時以開盤價計為劣勢停損（stop-gap）；停利與停損同日觸發時優先判定停損（adverse-stop-first）。程式實作均嚴格符合預先登記。
- **持有期與冷卻期（Cooldown）**：
  - 持有期為 10 個完整交易日，於第 11 個交易日開盤退場（time exit）。
  - 部位完全退場後，必須間隔 5 個完整 session 才能接受新訊號，時鐘錨點以平倉完成日（`completed-position-exit`）起算，實作邏輯無誤。
- **部位管理（Position Sizing）**：
  - 嚴格遵守預先計算成本後的 2% 淨值風控上限（`risk_fraction = 0.02`），以向下取整數股數建倉，無借款與槓桿操作。

---

## 4. Development 穩健度重算與分析

依據允許的 2013 年暖機與 2014–2018 年開發資料，完全重新計算各項指標：

### 4.1 基礎績效與退場分佈
- **總交易筆數**：24 筆（全數完成）。
- **Base 成本表現**：
  - 總報酬率：33.68%
  - 獲利因子（Profit Factor）：5.04
  - 實現資金最大回撤（Realized Drawdown）：2.00%
  - 勝率：83.33%（20 勝 4 敗）
  - 平均獲利：$2,100.96 / 平均虧損：-$2,085.75
- **Stress 壓力成本表現**：
  - 總報酬率：26.52%
  - 獲利因子：4.20
  - 實現資金最大回撤：2.12%
  - 勝率：75.00%（18 勝 6 敗，其中 2 筆微幅獲利之時間平倉被滑價與手續費侵蝕轉為小虧）
- **退場原因分佈**：
  - 觸及目標價（target）：8 筆
  - 跳空高開達標（target-gap）：7 筆
  - 10 日時間到期（time）：6 筆
  - 觸及停損價（stop）：3 筆
  - 跳空停損（stop-gap）：0 筆（相較於 price_only 的 1 筆）

### 4.2 逐年分段與獲利集中度
- **年度交易與損益分佈**：
  - **2014 年**：6 筆交易，Base PnL $8,442.90（佔比 25.07%），Stress PnL $6,895.76。
  - **2015 年**：5 筆交易，Base PnL $8,434.64（佔比 25.05%），Stress PnL $6,891.09。
  - **2016 年**：5 筆交易，Base PnL $4,633.52（佔比 13.76%），Stress PnL $3,340.53。
  - **2017 年**：2 筆交易，Base PnL $1,388.86（佔比 4.12%），Stress PnL $903.01。
  - **2018 年**：6 筆交易，Base PnL $10,776.23（佔比 32.00%），Stress PnL $8,492.79。
- **分析**：最大年度獲利佔比為 2018 年的 32.00%，符合低於 50% 集中度的限制。但 2017 年樣本嚴重萎縮至 2 筆，反映此均值回歸邏輯在多頭強勢上攻時極易陷入長期空手。

### 4.3 剔除單一年度檢驗（Leave-One-Year-Out）
- 逐一移除任一年度，其餘 4 年的表現：
  - 剔除 2014 年：18 筆，Stress 報酬率 18.36%，Profit Factor 3.41。
  - 剔除 2015 年：19 筆，Stress 報酬率 18.86%，Profit Factor 4.35。
  - 剔除 2016 年：19 筆，Stress 報酬率 22.91%，Profit Factor 4.90。
  - 剔除 2017 年：22 筆，Stress 報酬率 25.56%，Profit Factor 4.51。
  - 剔除 2018 年：18 筆，Stress 報酬率 18.03%，Profit Factor 4.17。
- **分析**：剔除任一年度後，Stress 獲利因子均能維持在 3.4 以上，回撤未超過 2.12%，顯示獲利並非完全由單一異常年份支撐；但剔除 2014 或 2018 年後剩餘筆數僅 18 筆，凸顯整體總量不足的結構問題。

### 4.4 參數敏感度與消融重算（關鍵發現）
經重算預先登記的 6 組參數擾動：
- `gap = 0.010`（偏離均線 1.0%）：28 筆，Base PF 2.51，Stress PF 2.13。
- `gap = 0.020`（偏離均線 2.0%）：19 筆，Base PF 8.55，Stress PF 6.58（交易筆數低於 20 筆門檻）。
- `rsi = 45`：22 筆，Base PF 5.78，Stress PF 4.68。
- `rsi = 55`：25 筆，Base PF 5.27，Stress PF 4.41。
- **`volume_spike_ratio = 1.00`**：25 筆，Base PF 3.86，Stress PF 3.25。
- **`volume_spike_ratio = 1.15`**：21 筆，Base PF 4.17，Stress PF 3.47。

> **核心洞察**：
> 當成交量門檻微降至 1.00 時，交易筆數變為 25 筆，多出來的正是 2018-04-09 那筆虧損交易（該日過去 5 日最高量比為 1.0078），此時績效直接回到未加成交量濾網的水準（PF 3.86）。這證實 1.05 的門檻設定主要是「剛好將 1.0078 擋在門外」，其餘 24 筆交易的量比皆輕鬆超越 1.05。

---

## 5. 調整優先順序建議

依據檢討規範，建議依性質明確分級：

### 5.1 規格／實作缺陷（最高優先修正）
1. **修正 `evidence/development.yml` 中機制消融的分支標籤**：
   - **預期解決問題**：消除 evidence 內部數值矛盾，確保記錄真實呈現「`calibrated_two_stage` 為 24 筆（PF 5.04）」與「`price_only` 為 25 筆（PF 3.86）」。
   - **驗收方式**：重新由驗證腳本自動產生並校對字典鍵值對應。

### 5.2 Development 警訊（需高度關注之設計脆弱點）
2. **謹慎看待 1.05 倍成交量濾網的真實保護效果**：
   - **實際問題**：1.05 倍門檻本質上是為了排除單一虧損交易（2018-04-09）的特定校準，缺乏跨期穩健性。
   - **預期影響**：在樣本外未知的市場環境中，該門檻極可能因行情微小噪聲而失效，無法持續提供過濾假止跌的保證。
   - **因應方案**：下一代 Study 若欲採用成交量濾網，不應仰賴微調單一靜態倍數，應設定更具容錯空間的機制。
3. **交易頻率緩衝空間不足之風險**：
   - **實際問題**：5 年 24 筆交易過度接近 20 筆的死線。在單邊強勢行情年（如 2017 年僅 2 筆），策略可能長期無法觸發。
   - **預期影響**：若評估期面臨類似環境，容易因成交筆數不足而直接失格。

### 5.3 未驗證設計假說（僅可納入後續新 Study 預先登記）
4. **探索具微觀經濟意義的換手確認機制**：
   - **機制假設**：改以當日換手率相對歷史百分位數（例如量能位於前 20%），或結合下影線比例（買盤承接力道）取代單純的 1.05 均量比。
   - **可否證驗收方式**：於新 Study 登記該規則，檢驗其在不同滾動區間內對各類虧損的平均抑制能力，而非僅看單一特殊交易。
5. **波動率動態調整停損／停利機制（ATR-based Stops）**：
   - **機制假設**：固定 4% 的停損與停利無法適應不同波動環境。改用例如 1.5 倍 ATR 作為停損與目標，或可在低波動期及時獲利，高波動期避免被雜訊掃出場。
   - **可否證驗收方式**：在新 Study 預先登記，並在相同 2% 風險預算下檢驗其獲利因子與最大回撤是否優於固定比例基準。

---

## 6. 不能得出的結論

基於封存式盲檢討的核心原則，本報告嚴格限制推論範圍，**明確聲明以下事項無法亦不得推導**：

1. **無法得知正式 Historical Evaluation 的實際成敗**：本檢討完全不知悉策略在 2020–2024 年評估期的表現。
2. **無法斷定正式評估若失敗是由上述哪項弱點造成**：即使策略在未公開的正式評估中失敗，也不能事後附會「必然是因為 1.05 倍成交量失效」或「筆數不足失格」。
3. **不保證修改建議能改善正式結果**：任何基於 Development 觀察提出的改進假說，未經新的不可變 Study 與盲測驗證前，皆不構成績效改善之保證。

---

## 7. 讀取紀錄與合規聲明

### 7.1 本次檢討實際讀取的檔案清單
1. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v009/manifests/preregistration.yml`
2. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v009/manifests/candidate-definition.yml`
3. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v009/manifests/qualification-spec.yml`
4. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v009/manifests/development-trial-inputs.yml`
5. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v009/manifests/source-bundle.yml`
6. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v009/manifests/data-snapshot-acquisition.yml`
7. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v009/evidence/development.yml`
8. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v009/evidence/development-authorization.yml`
9. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v009/evidence/provenance.yml`
10. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v009/evidence/selection-evidence.yml`
11. `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py`
12. `tests/test_tsm_mean_reversion_two_stage_volume_reversal_v009.py`
13. `.agents/skills/blind-review-strategy-study/references/review-method.md`

### 7.2 市場資料使用範圍
- `research/market-data/yahoo/TSM-2013-01-02-2025-12-31-auto-adjust--sha256-50178c8f2965b76b37f60e906901d2ec06e997e3c647df6b885bb99464788e95.csv`：僅切片讀取並使用 2013-01-01 至 2018-12-31（即 warmup 與 development 明確授權之日期範圍）。

### 7.3 合規性聲明
本次檢討嚴格遵守治理隔離規範，**完全沒有**讀取、搜尋或接觸以下禁止資源：
- `study.yml`（未查看 disposition 或 outcome）
- `historical-evaluation-artifacts/` 資料夾內任何內容
- `.super-admin/` 資料夾內任何內容
- `evidence/historical-evaluation*`、`evidence/terminal-evidence.yml`
- `events/000008-*` 及其後之事件檔、`journals/` 記錄
- 2019 年隔離期（Quarantine）與 2020–2024 年正式評估期之市場資料與結果
- 任何外部網路、券商連線或非公開資料庫
