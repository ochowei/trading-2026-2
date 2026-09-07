# Study 封存式盲檢討報告：tsm-mean-reversion-two-stage-volume-reversal--v010

本檢討報告依據專案規範與 `blind-review-strategy-study` 之檢討方法（[review-method.md](file:///Users/william/gitRepo/trading-2026-2/.agents/skills/blind-review-strategy-study/references/review-method.md)）撰寫。本報告為補充性封存筆記，不構成正式生命週期事件鏈之輸入，亦不改寫任何 digest。

---

## 1. 範圍與結論限制

- **研究流程（Workflow）**：`strategy-forward-replication-research--v001`
- **目標研究（Study ID）**：[`tsm-mean-reversion-two-stage-volume-reversal--v010`](file:///Users/william/gitRepo/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/)
- **執行角色**：`study 開發者`
- **檢討性質**：封存式檢討（Blind Review），嚴格恪守「零結果曝光」（Zero Result Disclosure）原則。
- **授權資料區間**：
  - **Warmup（指標暖機）**：`2013-01-01` 至 `2013-12-31`（僅用於計算 20 日移動平均線、2 日 RSI 及 20 日成交量均量之初始歷史狀態，嚴格禁止計入任何交易績效與訊號統計）。
  - **Development（策略開發）**：`2014-01-01` 至 `2018-12-31`（涵蓋 1,260 個交易日，所有進場、出場、交易紀錄、年度切分與穩健度壓力測試均嚴格限定於此區間）。
- **零結果曝光聲明**：
  - 本次檢討**完全未讀取、開啟、搜尋或引用** 2020–2024 年之正式 Historical Evaluation、Terminal 結果、`study.yml`、`historical-evaluation-artifacts/`、`.super-admin/`、`events/000008-*` 或任何非公開結果。
  - 本檢討**無法回答、亦不會推測**該策略在 2020–2024 年正式驗證期的成敗與真實損益。

---

## 2. 實際問題與影響

本節先以白話文清楚說明策略在設計與開發證據中所呈現的核心問題，再說明其在實際交易中的運作影響。

### 問題一：核心假說「成交量先行濾網」在 5 年開發期實質完全鈍化（沉睡條件，Sleeping Condition）

- **白話說明**：
  本策略的核心假說為「兩階段量先價行」——也就是在股價跌深反彈當天，要求過去 5 個交易日內必須先出現過一次成交量放大（單日成交量達過去 20 日均量的 1.05 倍以上），藉此過濾掉主力未進駐的「假止跌」反彈。
  然而，在事前設計的消融實驗（Mechanism Ablation）中，我們比對了「完整策略（`calibrated_two_stage`）」與「關閉成交量濾網、僅看價格反轉（`price_only`）」兩組設定：
  **兩者在 2014–2018 年間產生的 29 筆交易、進出場日期、持有天數與各項績效指標完全 100% 相同**（壓力報酬率皆為 26.59%、獲利因子皆為 3.21、最大回撤皆為 2.58%）。
- **實際影響**：
  這代表在台積電（TSM）短線跌破 20 日均線達 1.2% 且反彈收紅（Close > prior Close）的情境下，過去 5 天的成交量幾乎「必然」有一天會微幅超越 20 日均量（1.05 倍門檻過低）。
  在整整 5 年共 1,260 個交易日中，這道成交量濾網**沒有過濾掉任何一筆假反彈**。這意味著核心經濟假說在開發期根本沒有受到實質考驗，屬於「沉睡中的無效條件」。如果未來市場結構改變，此濾網要麼繼續形同虛設，要麼會在完全不可預期的時刻隨機剔除正常交易。

### 問題二：單邊強勢牛市（如 2017 年）交易機會依然過度稀疏，多頭長期空手偏誤仍未完全根除

- **白話說明**：
  相較於 v009 在 2017 年僅有 2 筆交易（面臨年度交易代表性不足的失格風險），v010 將均線乖離門檻由 1.5% 調降至 1.2%、RSI 上限放寬至 55，成功將 2017 年交易次數提升至 3 筆，整體交易總數提升至 29 筆（+20.8%）。
  然而，2017 年是全球半導體與台積電強勁單邊上漲的經典牛市。在整年約 252 個交易日中，策略僅進場 3 次，平均持倉約 6 天，換言之，整年有超過 92% 的時間資金處於閒置空手狀態。
- **實際影響**：
  均值回歸策略在強勢單邊多頭市場中，股價很少出現深幅拉回，因此進場訊號自然稀疏。雖然 2017 年的 3 筆交易全數獲利（壓力淨利 +2,955.19 美元），但 3 筆交易在統計上代表性極其薄弱。若在未來的驗證期再度遭遇長達一至兩年的強勁大多頭（例如 2020–2021 年半導體景氣大循環），策略可能面臨年交易數再度瀕臨門檻紅線、或資金使用效率極低的結構性瓶頸。

### 問題三：整體獲利高度依賴「隔夜跳空達標」（Target-Gap），對開盤搓合機制敏感度極高

- **白話說明**：
  在全部 29 筆交易中，有 8 筆交易是在開盤時直接向上跳空超越 4% 停利點出場（`target-gap`）。這 8 筆交易在壓力情境下貢獻了高達 19,475.88 美元的獲利，**佔全策略所有獲利交易毛利總和（36,981.72 美元）的 52.66%**。
- **實際影響**：
  TSM 為在美股掛牌的 ADR，其開盤價格高度受到台灣集中交易市場（TWSE: 2330）日間交易漲跌的直接傳導。策略超過一半的利潤並非來自美股常規交易時段的平滑推升，而是依賴開盤瞬間的跳空價格改善（price improvement）。一旦遇到開盤流動性緊縮、搓合滑價劣於預期、或台美現貨連動價差脫鉤，跳空所帶來的額外超額利潤可能大幅縮水。

### 問題四：固定 4% 停利停損缺乏對波動度環境的自適應彈性

- **白話說明**：
  策略採取固定的上下 4% 機制（進場價 +4% 限價停利、-4% 市價停損）。
- **實際影響**：
  固定百分比在低波動年度（如 2017 年 ATR 相對平緩）能夠穩定鎖定波段；但在高波動時期，4% 的空間可能在單日日內洗盤中就被過早觸發停損，使得「先停損後反彈」的噪聲風險上升。

---

## 3. 規格與實作檢查

本節對照凍結候選規格（[`candidate-definition.yml`](file:///Users/william/gitRepo/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/manifests/candidate-definition.yml)）、預先登記規格（[`preregistration.yml`](file:///Users/william/gitRepo/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/manifests/preregistration.yml)）、策略實作核心（[`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v010.py`](file:///Users/william/gitRepo/trading-2026-2/src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v010.py)）及單元測試清冊（[`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v010.py`](file:///Users/william/gitRepo/trading-2026-2/tests/test_tsm_mean_reversion_two_stage_volume_reversal_v010.py)）。

### 3.1 歷史規格缺陷之修復確認（已確認修復）

- **前版缺陷**：在 v009 盲檢討中曾指出，其 Development 報告生成腳本中的機制消融字典（`calibrated_two_stage` 與 `price_only`）發生鍵值顛倒之檔案缺陷。
- **本版確認**：經核對 v010 原始碼與生成證據，`calibrated_two_stage`（成交量開啟、價格反轉開啟）與 `price_only`（成交量關閉、價格反轉開啟）之參數結構與輸出字典已徹底修正對齊，無混淆情形。

### 3.2 實作與假說一致性檢驗

1. **決策時間與資訊隔離（No Look-ahead Bias）**：
   - 訊號計算錨定於 `completed-session-close`。
   - SMA(20) 與 2 日 RSI 僅取用當日與過去收盤價。
   - 成交量基準均量取用 `clean["Volume"].shift(1).rolling(20).mean()`，前置量增比率取用 `shift(1).rolling(5).max()`，嚴格確保訊號日的放量行為不會反向污染過去的量能基準，且量能判定嚴格發生於訊號日前。
2. **進場與搓合機制（Execution Alignment）**：
   - 次一交易日開盤價以市價單（Market Proposal）進場，符合真實交易不可預知次日盤中價格之約束。
   - 同 session 內若同時觸及停利與停損，程式碼嚴格執行「不利停損優先」（adverse-stop-first），杜絕樂觀偏差。
3. **退場與冷卻期（Cooldown Logic）**：
   - 持有期上限為 10 個完整交易 session，第 11 個 session 開盤執行時間退場（time exit）。
   - 平倉完成後，冷卻期時鐘錨定於 `completed-position-exit`，強制等待 3 個交易日且部位為空手（flat），邏輯與規格完全吻合。
4. **部位規模與資金管理（Position Sizing）**：
   - 每筆交易承擔名目資產 2% 之單筆風險預算，計算時已先扣除進出場手續費與滑價模型之最劣成本，且嚴格受限於現有可用現金（無槓桿、不借款）。
5. **單元測試驗證**：
   - 策略專屬測試集共 248 個測試案例，全數通過。涵蓋數值邊界、空值處理、同日停損停利衝突、退場冷卻重置等關鍵場景。

---

## 4. Development 穩健度重算

本節所有數據均由 [`evidence/development.yml`](file:///Users/william/gitRepo/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/evidence/development.yml) 原始交易紀錄與逐日曲線直接解析重算。

### 4.1 核心績效總覽（2014–2018）

| 評估維度 | 基礎成本情境 (Base Cost) | 壓力成本情境 (Stress Cost) | 預先登記門檻 (Required Gate) | 判定 |
| :--- | :---: | :---: | :---: | :---: |
| **完成交易筆數** | 29 筆 | 29 筆 | >= 20 筆 | 通過 |
| **總報酬率 (Compounded Return)** | +34.79% | +26.59% | > 0.0% | 通過 |
| **獲利因子 (Profit Factor)** | 3.84 | 3.21 | Base > 1.10 / Stress > 1.00 | 通過 |
| **已實現最大回撤 (Realized Trade MaxDD)** | 2.55% | 2.58% | <= 10.0% | 通過 |
| **逐日盯市最大回撤 (Mark-to-Market MaxDD)** | 3.49% | 3.69% | 診斷性參考 (<= 10.0%) | 穩健 |
| **單筆最大虧損比例** | 2.55% | 2.51% | <= 4.0% | 通過 |
| **交易勝率 (Win Rate)** | 79.31% (23/29) | 72.41% (21/29) | - | 優異 |
| **最長連續虧損** | 2 筆 | 2 筆 | - | 風險極低 |
| **平均持倉天數** | 6.34 個交易日 | 6.34 個交易日 | <= 10 個交易日 | 符合設定 |

*註：壓力成本（Stress Cost）設定為單邊手續費 2 bps、單邊滑價 20 bps；基礎成本（Base Cost）為單邊手續費 1 bps、單邊滑價 5 bps。*

### 4.2 退場原因分佈與損益貢獻度（壓力情境）

| 退場型態 (Exit Reason) | 交易筆數 | 筆數佔比 | 壓力損益總額 (USD) | 佔獲利交易毛利比例 |
| :--- | :---: | :---: | :---: | :---: |
| **開盤跳空停利 (target-gap)** | 8 筆 | 27.59% | +19,475.88 | **52.66%** |
| **盤中限價停利 (target)** | 9 筆 | 31.03% | +16,482.16 | **44.57%** |
| **時間期滿退場 (time)** | 8 筆 | 27.59% | +1,023.68 | 2.77% |
| **盤中觸及停損 (stop)** | 3 筆 | 10.34% | -7,253.75 | - |
| **開盤跳空停損 (stop-gap)** | 1 筆 | 3.45% | -3,137.55 | - |
| **合計** | **29 筆** | **100.0%** | **+26,590.41** | **毛利: +36,981.72** |

### 4.3 年度切分與集中度分析（by_signal_year）

| 年度 | 交易筆數 | 基礎損益 (USD) | 壓力損益 (USD) | 壓力損益佔比 | 正報酬狀態 |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **2014** | 6 | +8,442.90 | +6,895.76 | 25.93% | 正報酬 |
| **2015** | 6 | +10,803.66 | +8,866.72 | 33.35% | 正報酬 |
| **2016** | 6 | +3,804.38 | +2,402.66 | 9.04% | 正報酬 |
| **2017** | 3 | +3,903.50 | +2,955.19 | 11.11% | 正報酬 |
| **2018** | 8 | +7,835.39 | +5,470.08 | 20.57% | 正報酬 |

- **集中度檢驗**：單一年度最高獲利佔比為 2015 年的 33.35%，未超過 50% 集中度預警防線。
- **交易年份數**：5 年皆有交易，且 5 年皆為正報酬（100% 正報酬年度）。

### 4.4 逐年剔除交叉檢驗（Leave-One-Year-Out, LOYO）

| 剔除年度 | 剩餘交易筆數 | 壓力報酬率 | 壓力獲利因子 (PF) | 壓力最大回撤 | 通過判定 |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **剔除 2014** | 23 筆 | +18.42% | 2.65 | 2.58% | 通過 |
| **剔除 2015** | 23 筆 | +16.89% | 2.88 | 2.51% | 通過 |
| **剔除 2016** | 23 筆 | +24.02% | 3.65 | 2.51% | 通過 |
| **剔除 2017** | 26 筆 | +23.50% | 3.15 | 2.58% | 通過 |
| **剔除 2018** | 21 筆 | +21.12% | 4.33 | 2.58% | 通過 |

- **結論**：任一年度剔除後，壓力報酬率皆維持在 16.8% 以上，獲利因子皆高於 2.65，回撤穩定在 2.58% 以內，證實策略獲利並非由單一暴利年度所驅動。

### 4.5 區塊重抽樣分析（Block Bootstrap, 50,000 次重複）

| 抽樣區塊長度 | 正報酬機率 | 獲利因子 > 1 機率 | 回撤 > 10% 機率 | 壓力報酬率 [5%, 50%, 95%] | 獲利因子 [5%, 50%, 95%] |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **3 筆交易區塊** | 99.97% | 99.97% | 0.002% | [12.98%, 26.63%, 41.89%] | [1.81, 3.37, 8.19] |
| **5 筆交易區塊** | 99.96% | 99.96% | 0.004% | [12.66%, 26.73%, 41.69%] | [1.81, 3.37, 7.81] |

- **日曆區塊抽樣（Calendar Block Bootstrap, 10,000 次重複）**：
  - 63 交易日區塊（約一季）：正報酬率 99.88%，回撤 > 10% 比例僅 0.05%。
  - 126 交易日區塊（約半年）：正報酬率 99.87%，回撤 > 10% 比例為 0.00%。

### 4.6 機制消融實驗比對（Mechanism Ablation）

| 實驗分支 | 條件設定 | 交易數 | 壓力報酬率 | 壓力獲利因子 | 壓力最大回撤 |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`calibrated_two_stage` (完整候選)** | 價均線負乖離 + RSI <= 55 + 反轉收紅 + 前 5 日量增 | 29 | +26.59% | 3.21 | 2.58% |
| **`price_only` (純價格反轉)** | 價均線負乖離 + RSI <= 55 + 反轉收紅 (關閉量增) | 29 | +26.59% | 3.21 | 2.58% |
| **`volume_only` (純量能均值回歸)** | 價均線負乖離 + RSI <= 55 + 前 5 日量增 (無收紅確認) | 50 | +5.37% | 1.14 | 8.27% |
| **`simple_baseline` (簡單均值回歸)** | 價均線負乖離 + RSI <= 55 (無反轉收紅、無量增) | 54 | +4.23% | 1.09 | 9.65% |

- **消融關鍵結論**：
  1. 「反轉收紅確認（`Close > prior Close`）」是大幅提升策略勝率與績效的關鍵機制（交易數由 54 筆精簡至 29 筆，壓力報酬由 4.23% 飆升至 26.59%，獲利因子由 1.09 提升至 3.21）。
  2. 「成交量先行濾網」在 1.05 倍門檻與 5 日窗口下，**完全沒有產生任何邊際過濾效果**（與 `price_only` 數據 100% 重合）。

---

## 5. 調整優先順序建議

針對上述發現，依專案規範劃分為三級建議，提供未來潛在新研究版本之調整依據：

### 5.1 規格／實作缺陷（最高優先級）

- **現狀**：**無未修復之規格或實作缺陷**。
  - v009 之機制消融鍵值顛倒已於 v010 正式修正。
  - 指標無未來資訊洩漏、搓合時間序列嚴謹、單元測試 248 項全數通過。

### 5.2 Development 警訊（中優先級）

1. **警訊一：成交量先行條件過度寬鬆導致機制鈍化**
   - **預期解決問題**：釐清成交量是否真有實質過濾價值，避免模型背負無實質作用的沉睡參數。
   - **具體建議**：若下一輪研究仍希望保留成交量假說，應探索提高量能放大倍數（例如 `volume_spike_ratio >= 1.15` 或 `1.20`），或將前置窗口縮短（例如由 5 日改為 2–3 日）；若提高門檻後證實無法進一步提升勝率或降低回撤，則應承認該假說在 TSM 上可能不具增量價值，並考慮正式精簡為純價格反轉策略。
   - **潛在副作用**：提高門檻必然導致交易筆數減少，可能再度使 5 年交易次數逼近 20 筆之失格紅線。
   - **可否證驗收方式**：若提高量增門檻後，所過濾掉的交易中「虧損交易比例顯著高於獲利交易比例」（使整體獲利因子與勝率進一步提升），則假說成立；反之若剔除的都是獲利交易，則應否證量能機制並予廢除。
2. **警訊二：跳空達標（Target-Gap）依賴度高達 52.7% 之開盤搓合脆弱性**
   - **預期解決問題**：防範美股開盤集合競價搓合時的極端滑價侵蝕利潤。
   - **具體建議**：在壓力測試中引入更嚴格的「開盤跳空折扣挑戰（Gap-Haircut Challenge）」，例如假設跳空幅度僅能吃到 50%~70% 的開盤價差，檢驗策略獲利因子是否仍能維持在 1.5 以上。
   - **潛在副作用**：僅為壓力評估，不改變實際交易邏輯。

### 5.3 未驗證設計假說（低優先級，僅可於新 Study 預先登記）

1. **假說 A：多頭環境自適應均線負乖離門檻（Bull-Regime Adaptive Gap）**
   - **機制說明**：針對 2017 年強勢多頭僅有 3 筆交易的問題，建立市場趨勢狀態判斷。當 20 日均線位於 60 日均線之上（多頭排列）時，適度將進場負乖離門檻由 1.2% 放寬至 0.8%~1.0%，以在強勢多頭中適度增加健康回檔的進場機會。
   - **注意事項**：此項機制可能增加多頭高檔震盪接刀的風險，必須在獨立的新 Study 中完整預先登記與驗證，不可任意植入現有流程。
2. **假說 B：真實波動區間（ATR）自適應動態停損停利**
   - **機制說明**：以 2.0 倍 14 日 ATR 取代固定的 4% 停利與停損，以適應不同年代的市場波動度膨脹與收縮。

---

## 6. 不能得出的結論

基於封存式盲檢討方法之核心倫理與科學界限，明確宣告以下**絕對不能得出**的推論：

1. **不能推斷正式 Historical Evaluation 的成敗**：
   本報告指出成交量濾網鈍化、跳空依賴度高及牛市交易少，**不代表**策略在 2020–2024 年正式驗證期一定失敗或已經失敗。同樣地，Development 的 3.21 高壓力獲利因子**亦不能保證**策略在正式評估期必然通過。
2. **不能將設計風險直接等同於未來市場失效**：
   成交量條件在 2014–2018 年未發揮過濾效果，僅代表在該特定 5 年的跌深反彈樣本中量能條件普遍滿足；這無法反推在 2020–2024 年（包含 2020 年新冠疫情劇震、2022 年大幅升息回檔等極端波動）中量能條件也會維持相同特性。
3. **不能宣稱修改建議必定能改善正式結果**：
   任何關於調整參數或簡化機制的建議，均屬未經未來資料驗證的設計推測，絕不可作為既成事實。

---

## 7. 讀取紀錄與合規聲明

### 7.1 本次檢討實際讀取檔案清冊

1. **檢討技能與方法規範**：
   - [`.agents/skills/blind-review-strategy-study/SKILL.md`](file:///Users/william/gitRepo/trading-2026-2/.agents/skills/blind-review-strategy-study/SKILL.md)
   - [`.agents/skills/blind-review-strategy-study/references/review-method.md`](file:///Users/william/gitRepo/trading-2026-2/.agents/skills/blind-review-strategy-study/references/review-method.md)
2. **研究規格與清冊**：
   - [`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/manifests/preregistration.yml`](file:///Users/william/gitRepo/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/manifests/preregistration.yml)
   - [`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/manifests/candidate-definition.yml`](file:///Users/william/gitRepo/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/manifests/candidate-definition.yml)
   - [`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/manifests/development-trial-inputs.yml`](file:///Users/william/gitRepo/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/manifests/development-trial-inputs.yml)
   - [`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/evidence/selection-evidence.yml`](file:///Users/william/gitRepo/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/evidence/selection-evidence.yml)
   - [`workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/evidence/development.yml`](file:///Users/william/gitRepo/trading-2026-2/workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v010/evidence/development.yml)
3. **策略原始碼與測試清冊**：
   - [`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v010.py`](file:///Users/william/gitRepo/trading-2026-2/src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v010.py)
   - [`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v010.py`](file:///Users/william/gitRepo/trading-2026-2/tests/test_tsm_mean_reversion_two_stage_volume_reversal_v010.py)

### 7.2 合規聲明

本次封存式檢討嚴格遵守專案權限與盲檢討規範：
- **未曾讀取、搜尋或引用**：
  - `study.yml`
  - `historical-evaluation-artifacts/`
  - `.super-admin/`
  - 任何 `README.md`
  - `evidence/historical-evaluation*` 或 `evidence/terminal-evidence.yml`
  - `events/000008-*` 及其後事件、`journals/`、terminal payload 與 evaluation payload
  - 任何 Full、Quarantine 或 2020–2024 年正式價格資料
  - 任何其他 Study 之研究內容
  - 外部網路、券商資訊或外部市場行情
- 全文完全由授權之 Warmup/Development 證據與事前規格獨立重算完成。
