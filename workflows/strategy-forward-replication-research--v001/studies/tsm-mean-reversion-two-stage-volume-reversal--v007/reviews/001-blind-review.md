# Study 封存式盲檢討報告：tsm-mean-reversion-two-stage-volume-reversal--v007

- **檢討編號**：`reviews/001-blind-review.md`
- **目標 Study**：`tsm-mean-reversion-two-stage-volume-reversal--v007`
- **所屬 Workflow**：`strategy-forward-replication-research--v001`
- **檢討角色**：`study 開發者`
- **檢討日期**：2026-09-07

---

## 1. 範圍與結論限制

本檢討為嚴格的**封存式盲檢討（Blind Review）**。

1. **資料與時間邊界**：本檢討僅允許使用該 Study 在預先登記階段（Preregistration）、候選人凍結（Candidate Freeze）以及 Development 階段所產生的公開規格、實作程式碼、單元測試，以及 2013 年暖機（Warmup-only）與 2014–2018 年開發階段（Development）之歷史數據與重算結果。
2. **零結果曝光保證**：本檢討**絕對沒有讀取、引用、搜尋或推測** 2020–2024 年正式 Historical Evaluation 或 Terminal 階段之任何成果、指標、損益、交易記錄或失敗原因。
3. **推論限制**：本報告指出的所有設計弱點與潛在風險，皆屬於事前可識別之理論與樣本內特性，不得被詮釋為「已證實的正式失敗原因」，本報告提出的任何改善建議亦不保證在正式評估環境中必然改善結果。

---

## 2. 實際問題與影響（白話解析）

先說核心問題與實際造成的市場後果，再談技術細節：

### 問題一：5 年只有 25 筆交易，樣本量極低且隨機性極高
- **白話說明**：在 2014 到 2018 整整五個日曆年（共 1,258 個美股交易日）中，策略總共只做了 25 筆交易，平均一年僅 5 筆；在 2017 年的多頭行情中，甚至整整一年只進場了 2 筆。
- **實際影響**：研究規範明訂「完成交易數必須達到 20 筆以上」。25 筆交易僅僅比生死線多了 5 筆。只要未來市場出現長期穩定上漲（導致價格很少跌破均線 1.5%）或極度平靜的盤整，五年間只要少掉 6 筆訊號，策略就會因為「交易次數不足」直接被系統淘汰判定失格，根本無法檢驗其獲利假說是否成立。

### 問題二：近三分之一的總獲利來自兩筆好運的「隔夜跳空大漲」
- **白話說明**：策略在壓力成本下 5 年總獲利約 23,961 美元，但光是 2015 年 1 月 14 日那一筆（Trade 007），就因為隔夜開盤直接大漲跳空超過 9%，一筆賺進 4,310 美元（佔總利潤 18.0%）；如果再加上 2018 年底的 Trade 024（跳空大賺 3,009 美元），這兩筆跳空交易就佔了全策略 5 年獲利的 30.5%！
- **實際影響**：台積電 ADR（TSM）在美股開盤前，其現貨已經在台灣市場交易完成，因此美股開盤極易產生大幅「跳空」。在 Development 階段中，策略有 8 筆交易因為向上跳空高於 4% 目標價而在開盤被「送分」出場（target-gap）；但向下跳空的停損卻只有 1 筆。如果未來遇到國際情勢逆轉、台股開盤重挫導致 ADR 頻繁向下跳空，跳空停損（stop-gap）將直接跌破設定的 4% 防線，造成遠大於預期的單筆本金衝擊。

### 問題三：「2 日 RSI <= 50 ＋ 收紅止跌」在數學上其實是「假止跌弱勢夾層」，排除了所有強勢反彈
- **白話說明**：策略假說原本以為自己是用「RSI 指標超賣」加上「今天收盤價比昨天高（止跌反轉）」做為進場濾網。但在代數上，2 日的簡單平均 RSI 只要遇到今天收紅，要小於等於 50，就**百分之百等價於：今天的上漲幅度不能超越昨天的下跌幅度**（也就是：前天下跌、昨天大跌、今天小漲但收盤價仍然低於前天）。
- **實際影響**：策略在數學上**完全封殺了強勁的 V 型反轉**！如果今天市場出現強烈止跌力道，一舉收復前一天的跌幅，RSI(2) 就會立刻跳破 50，策略就會當作沒看見而放棄進場；策略唯一會買進的，恰恰是「反彈力道疲弱、連昨天跌幅都收不復」的弱勢格局。這與策略假說所宣稱的「均值回歸與止跌確認」在經濟意涵上有明顯落差。

### 問題四：移除成交量尖峰濾網（v007 的唯一變更）雖然補足了交易數，但獲利品質嚴重劣化
- **白話說明**：v007 相較於 v006 唯一的改動，就是把「訊號日前 5 天內必須出現成交量尖峰」的條件關閉。消融實驗顯示：保留成交量條件時（v006），壓力 Profit Factor 高達 5.00；關閉成交量條件後（v007），交易次數從 20 筆增加到 25 筆，但 Profit Factor 直接崩跌到 3.25。
- **實際影響**：多出來的 5 筆交易品質顯著較差。成交量並非無用的雜訊，它在原本的設計中成功過濾掉了「沒有買盤換手力道支撐的死貓跳」。v007 雖然換取了多 5 筆的緩衝空間，卻實質犧牲了交易品質。

### 問題五：固定的 4% 停利停損未隨波動度調整，面臨制度性脆弱
- **白話說明**：TSM 股價在 2014 年約 12–15 美元，到了 2018 年約 35 美元，而在 2020 年後價格更是數倍於此。在股價與市場波動度完全不同的時期，一律死守「4% 停利、4% 停損、持有滿 10 天就走」的僵化架構。
- **實際影響**：低波動環境下，10 天根本跑不出 4% 的空間，大部分交易會被迫拖到時間截止以微利或手續費虧損出場；高波動環境下，單日內 4% 的震盪可能在進場當天就被隨機雜訊掃出場。

---

## 3. 規格與實作檢查

經過逐行比對 `manifests/preregistration.yml`、`manifests/candidate-definition.yml`、`manifests/development-trial-inputs.yml`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v007.py` 與單元測試：

### (A) 已確認之規格與清冊缺陷（可直接驗證之客觀問題）

1. **`development-trial-inputs.yml` 遺漏關鍵開關 `volume_lead_enabled: false`**：
   - 在 `candidate-definition.yml` 中，明確記錄 `volume_leads_price.enabled: false`；
   - 然而在 `development-trial-inputs.yml` 第 55–63 行中，清單列出了 `volume_average_length: 20`、`volume_lead_window: 5`、`volume_spike_ratio_minimum: '1.25'`，卻漏掉了 `volume_lead_enabled: false` 這一布林開關；
   - 雖然策略引擎程式中 `DEFAULT_SPEC.volume_lead_enabled` 預設值為 `False`，使得實際執行的回測邏輯吻合，但 manifest 自身表達不完整，易使讀取 trial inputs 的驗證器或協作者誤判為成交量開關處於啟用狀態。
2. **`_required_history_sessions` 冗餘保留成交量暖機長度**：
   - 策略程式 `tsm_mean_reversion_two_stage_volume_reversal_v007.py` 第 258–265 行之 `_required_history_sessions` 寫死計算 `volume_average_min_periods + volume_lead_min_periods`（20 + 5 = 25）。
   - 儘管策略已關閉成交量，歷史長度檢查仍依賴已停用指標的長度。因其剛好等於 `fold_warmup_sessions: 25`，未造成執行錯誤，但程式碼與規格存在邏輯耦合殘留。

### (B) 純設計風險（程式無誤，但經濟與結構邏輯薄弱）

1. **RSI(2) 簡單滾動平均之代數退化**：
   - 程式嚴格按照 preregistration 登記的 `simple-rolling-mean` 實作：
     $$\text{gain} = \text{rolling\_mean}(\Delta Close^+, 2),\quad \text{loss} = \text{rolling\_mean}(\Delta Close^-, 2)$$
   - 當今日收盤上漲（$\Delta Close_t > 0$）時，要滿足 $RSI(2) \le 50$，必然需要 $\text{gain} \le \text{loss}$，即：
     $$\Delta Close_t \le -\Delta Close_{t-1} \implies Close_t - Close_{t-1} \le Close_{t-2} - Close_{t-1} \implies Close_t \le Close_{t-2}$$
   - 這證實了本策略所採用的並非一般技術分析認知的「動量超賣震盪指標」，而是純粹的「前日大跌、今日小漲未破前天」的三棒特殊形態。
2. **冷卻期（Cooldown）機制對單一標的交易頻率的壓制**：
   - 策略設定 `cooldown_sessions: 5`，時鐘起點為 `completed-position-exit`。
   - 每一筆交易最長持倉 10 日，出場後強制休眠 5 日，單一循環最短需 15 個交易日。這使得一年至多僅能承載約 16 筆交易，極度壓縮了訊號容量。
3. **部位風險模型（Position Sizing Risk Budget）之有效性**：
   - 程式實作了嚴格的現金上限與 2% 風險預算計算：
     $$\text{shares} = \min\left(\lfloor \text{cash} / \text{entry\_cash\_per\_share} \rfloor,\; \lfloor (\text{cash} \times 0.02) / \text{modeled\_loss\_per\_share} \rfloor\right)$$
   - 在 4% 停損與費用滑價下，單筆最大損失受控在 ~2.0% 資金之內，實作嚴謹，未放大槓桿。

---

## 4. Development 穩健度重算數據

從 `evidence/development.yml` 重算與核實之客觀數據如下：

### (A) 核心績效指標（2014–2018，共 1,258 個 session）

| 指標名稱 | Base 成本模型 (slippage 5 bps, fee 1 bps) | Stress 成本模型 (slippage 20 bps, fee 2 bps) | 門檻要求 | 結果判定 |
| :--- | :--- | :--- | :--- | :--- |
| **完成交易數 (Completed Trades)** | 25 | 25 | $\ge 20$ | 通過 |
| **涵蓋年數 (Traded Years)** | 5 | 5 | $\ge 3$ | 通過 |
| **總累積報酬 (Return)** | +30.97% | +23.96% | $> 0$ | 通過 |
| **獲利因子 (Profit Factor)** | 3.86 | 3.25 | $> 1.10$ (Base) / $> 1.00$ (Stress) | 通過 |
| **已實現最大回撤 (Max Drawdown)** | 2.03% | 2.12% | $\le 10.0\%$ | 通過 |
| **每日 Low 估值回撤 (MTM Max DD)** | 3.30% | 3.53% | 診斷指標 | 通過 |
| **單筆最大損失比率 (Max Loss Fraction)**| 2.03% | 2.02% | $\le 4.0\%$ | 通過 |
| **勝率 (Win Rate)** | 76.0% (19 勝 / 6 負) | 68.0% (17 勝 / 8 負) | 無正式門檻 | 良好 |

### (B) 出場原因分佈統計

- **達到目標出場（Target Hit）**：
  - 一般盤中觸及 +4% 限價 (`target`)：**7 筆** (28.0%)
  - 隔夜開盤跳空超越 +4% (`target-gap`)：**8 筆** (32.0%)
  - **合計達成目標**：**15 筆** (60.0%)
- **停損出場（Stop Hit）**：
  - 盤中跌破 -4% 市價停損 (`stop`)：**3 筆** (12.0%)
  - 開盤跳空跌破 -4% 停損 (`stop-gap`)：**1 筆** (4.0%)
  - **合計停損**：**4 筆** (16.0%)
- **時間到期出場（Time Exit）**：
  - 持滿 10 個 session 後於第 11 日開盤市價退出 (`time`)：**6 筆** (24.0%)
  - 在 Stress 成本下，6 筆時間出場中有 3 筆微幅獲利、3 筆微幅虧損。

### (C) 年度分段與獲利集中度（Signal Year Breakdown）

| 年度 | 交易筆數 | Base PnL ($) | Stress PnL ($) | Stress 獲利佔比 | 備註 |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **2014** | 6 | 8,442.90 | 6,895.76 | 28.8% | 穩定貢獻 |
| **2015** | 5 | 8,434.64 | 6,891.09 | 28.8% | 含單筆大賺跳空 (Trade 007, +$4,310) |
| **2016** | 5 | 4,633.52 | 3,340.53 | 13.9% | 穩定貢獻 |
| **2017** | **2** | 1,388.86 | 903.01 | **3.8%** | **極度枯竭（整年僅 2 筆交易）** |
| **2018** | 7 | 8,067.43 | 5,930.95 | 24.8% | 含 Trade 024 跳空 (+$3,009) |
| **總計** | **25** | **30,967.35** | **23,961.33** | **100.0%** | 2014+2015 貢獻達 57.6% |

### (D) Leave-One-Year-Out (LOYO) 穩健度（逐年抽離測試，Stress 模型）

| 抽離年度 | 剩餘交易數 | 抽離筆數 | 剩餘總報酬 | 剩餘獲利因子 (PF) | 剩餘最大回撤 | 通過標準 (Return>0, PF>1, DD<=10%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **抽離 2014** | **19** | 6 | +15.96% | 2.62 | 2.12% | 全部通過（但交易數落入 <20） |
| **抽離 2015** | 20 | 5 | +16.45% | 3.09 | 2.02% | 全部通過 |
| **抽離 2016** | 20 | 5 | +20.43% | 3.49 | 2.02% | 全部通過 |
| **抽離 2017** | 23 | 2 | +23.01% | 3.39 | 2.12% | 全部通過 |
| **抽離 2018** | **18** | 7 | +18.03% | 4.17 | 2.12% | 全部通過（但交易數落入 <20） |

### (E) 機制消融對照（Mechanism Ablation Arms）

| 消融分支名稱 | 核心規則差異 | 完成交易數 | Stress 總報酬 | Stress PF | Stress 最大回撤 | 實質意義 |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`full_two_stage` (v006)** | 價行確認 ＋ 成交量尖峰 | 20 | +22.31% | **4.995** | 2.12% | 獲利因子最高，防禦力最強 |
| **`price_only_candidate` (v007)** | 僅價行確認（**本輪候選**） | **25** | **+23.96%** | **3.249** | 2.12% | 筆數增加 5 筆，但 PF 明顯衰退 |
| **`volume_only`** | 僅成交量尖峰，無價行確認 | 36 | +6.95% | 1.280 | 6.07% | 缺乏價行止跌時表現疲弱 |
| **`simple_baseline`** | 無成交量、無價行確認 | 44 | +1.80% | 1.050 | 7.69% | 幾乎無法克服交易成本摩擦 |

---

## 5. 調整優先順序與分類建議

依據盲檢討規範，建議依據嚴格分為三類：

### 第一類：規格／實作缺陷（不需市場結果即可確認，優先度最高）
1. **補正 `development-trial-inputs.yml` 之布林開關**：
   - *預期解決問題*：消除 `candidate-definition.yml`（寫明 `enabled: false`）與 `development-trial-inputs.yml`（漏列開關卻保留參數）之間的不一致性。
   - *驗收方式*：Schema 驗證時確認 `volume_lead_enabled` 必須與候選定義完全匹配。
2. **解耦指標計算中未啟用條件之暖機依賴**：
   - *預期解決問題*：修改 `_required_history_sessions`，使其在 `volume_lead_enabled == False` 時僅需計算 SMA 與 RSI 之暖機期（20 日），提升程式邏輯的獨立性。

### 第二類：Development 警訊（由樣本內分段與集中度支持，下一輪優先處理）
1. **解決交易次數邊緣化（5 年僅 25 筆）問題**：
   - *預期解決問題*：防止在低波動或單邊多頭年份（如 2017 年僅 2 筆）因交易量不足 20 筆而直接失效。
   - *潛在副作用*：若單純放寬條件（例如將均線負偏離由 1.5% 降至 1.0%），可能引來更多偽訊號，降低獲利因子。
   - *驗收方式*：在下一輪研究中預先登記負偏離參數變體，驗證交易數提升至 35–50 筆時，Stress PF 是否仍可大於 1.50。
2. **審視隔夜跳空（Target-Gap）對整體績效的過度扭曲**：
   - *預期解決問題*：目前總獲利有 30.5% 集中於 2 筆有利的開盤向上跳空。需防範未來若遭遇向下的隔夜跳空，會否造成超出風險預算的連續大幅虧損。
   - *驗收方式*：在 Challenge 階段之 Worse-fills 與 Higher-costs 中，對跳空出場額外施加懲罰性滑價測試。

### 第三類：未驗證設計假說（具合理經濟機制，但需新 Study 預先登記）
1. **重新評估成交量濾網（Volume Lead）之價值**：
   - *設計機制*：消融實驗證明加入成交量後，Stress PF 由 3.25 躍升至 5.00，證明成交量具備過濾劣質假止跌的實質功能。下一輪可考慮調整成交量尖峰倍率（如從 1.25 調降至 1.15）或縮短前置窗口，尋求「兼顧交易筆數與高品質過濾」的折衷方案。
2. **改用 Wilder 平滑 RSI 或明確之 K 線價行條件**：
   - *設計機制*：目前 RSI(2) 的 2 日簡單平均在數學上畸形地限制了「今日反彈不得超越昨日跌幅」。下一輪可嘗試標準的 Wilder's RSI(2) 或直接定義「收盤突破前日高點」等明確的價行形態，回歸真正的均值回歸與止跌確認假說。
3. **引進 ATR 動態停利停損機制**：
   - *設計機制*：以 2x 14-day ATR 取代固定的 4.0% 上下界，以動態調適台積電在不同歷史時期（15 美元 vs 100 美元以上）的真實市場波動。

---

## 6. 不能得出的結論

為維持研究科學性與防範後見之明偏誤，本次檢討特別宣告：

1. **無法判斷正式 Historical Evaluation 的成敗或失敗原因**：本檢討完全未開啟正式評估結果，不得因為 Development 階段績效良好（PF 3.25、回撤 2.12%）就斷言正式評估必然通過；亦不得因為指出設計缺陷就推斷正式評估必定死於該缺陷。
2. **不能斷言隔夜跳空優勢必然持續**：8 筆 target-gap 對比 1 筆 stop-gap 是 2014–2018 年的歷史樣態，無法保證未來跨時區交易的跳空方向永遠偏向多方。
3. **不能保證任何建議修改均能改善成果**：本報告提出之所有調整方向（如 ATR 動態止盈止損、成交量門檻調降）均屬未經否證之新假說，必須於全新 Study 中完整完成預先登記後始得驗證。

---

## 7. 讀取檔案紀錄與零曝光宣告

### 本次實際讀取之檔案清單

1. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v007/manifests/preregistration.yml`
2. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v007/manifests/candidate-definition.yml`
3. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v007/manifests/qualification-spec.yml`
4. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v007/manifests/development-trial-inputs.yml`
5. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v007/manifests/source-bundle.yml`
6. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v007/manifests/data-snapshot-acquisition.yml`
7. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v007/evidence/development.yml`
8. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v007/evidence/development-authorization.yml`
9. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v007/evidence/provenance.yml`
10. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v007/evidence/selection-evidence.yml`
11. `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v007.py`
12. `tests/test_tsm_mean_reversion_two_stage_volume_reversal_v007.py`
13. `research/tsm-mean-reversion-two-stage-volume-reversal--v007/run_development.py`

### 嚴格零曝光宣告

本人（以 `study 開發者` 角色）嚴正聲明：
- 本次檢討**完全沒有開啟、搜尋、讀取或使用**目標 Study 之 `study.yml`、`historical-evaluation-artifacts/` 資料夾、`.super-admin/` 資料夾、`evidence/historical-evaluation*`、`evidence/terminal-evidence.yml`、`events/000008-*` 及其後之事件檔案、`journals/` 日誌，以及 2020–2024 年之任何價格快照或正式評估產物。
- 本報告亦未進行全域文字搜尋、未執行 Git diff/log 歷史查詢、亦未連線外部網路或券商資料。
- 本檢討報告係獨立於正式結果之外完成之封存式分析。
