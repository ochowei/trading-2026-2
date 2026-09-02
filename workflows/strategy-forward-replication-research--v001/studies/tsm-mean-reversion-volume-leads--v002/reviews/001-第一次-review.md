# TSM Mean Reversion Volume Leads v002：封存式盲檢討

編號：第一次 review

檢討日期：2026-09-02

## 一、範圍與限制

- Workflow 固定為 `strategy-forward-replication-research--v001`。
- 目標 Study：`tsm-mean-reversion-volume-leads--v002`。
- Warmup 期間：2013 年。
- Development 期間：2014-01-01 至 2018-12-31。
- 本報告只使用研究設計、策略程式、測試、Development 證據，以及同名的 warmup／Development 快照。
- 沒有讀取或使用正式 Evaluation、challenge、replay、terminal 結果，也沒有使用網路、外部市場資料或 connector。

這是一份封存式盲檢討，因此不能回答正式 Evaluation 為什麼成功或失敗，也不把 Development 警訊當成正式結果的失敗原因。

## 二、結論先講

這個 Study 在 Development 階段不是「整體正報酬、只等待正式驗證」的狀態，而是已經顯示出明確脆弱性：

1. Stress 下的總體優勢很薄。
2. 穩健度高度依賴 2015 年。
3. 連續區塊重抽樣與逐年留一檢查都沒有支持穩定性。
4. 程式大致重現了預先登記的規則，但 RSI 的定義、有效 warmup 與 provenance 文件仍有可重現性問題。

## 三、Development 表現與實際影響

| 指標 | Base | Stress |
|---|---:|---:|
| 完成交易 | 29 | 29 |
| 報酬 | 6.86% | 2.03% |
| Profit factor | 1.294 | 1.088 |
| 最大回撤 | 6.40% | 6.77% |
| 最大單筆已實現損失 | 2.30% | 2.27% |

主要警訊如下：

- Stress block bootstrap 的正報酬比例只有 60.0%–61.3%，低於預先登記的 80% gate。
- Stress 下回撤超過 10% 的重抽樣比例為 20.4%–25.0%，高於 10% 上限。
- Leave-one-signal-year-out 移除 2015 年後，stress profit factor 為 0.968、報酬為 -0.459%，同時未通過最低 profit factor 與最低報酬要求。
- 2015 年有 11/29 筆交易，stress 淨損益約 2,470；2014 與 2016 年為負，2017 與 2018 年只有小幅正貢獻。
- Stress 報酬比 base 少 4.83 個百分點，約失去 base 報酬的 70%。13 筆 target／target-gap 交易貢獻約 92% 的 stress 毛利，顯示優勢對成交成本與出場路徑相當敏感。

因此，Development 支持的說法只能是「這組固定規則在這段資料上有正的樣本內結果」，不能升級成「已證明有穩健的量先於價優勢」。

## 四、假說與規則的設計檢查

### 4.1 成交量條件比較像 setup，不是 trigger

規則只要求訊號日前 5 個 session 內曾出現一次成交量至少為過去 20 日平均量 1.25 倍的事件，沒有要求成交量事件具方向性，也沒有要求之後出現真正的反轉或價格確認。

這會造成兩個後果：

- 一次異常成交量在最多 5 個訊號日內持續有效，可能已經失去即時意義。
- 同一條件可能同時涵蓋恐慌換手與下跌中的派發，經濟意義不唯一。

下一輪應把「成交量先行」視為待驗證假說，而不是已確認的因果訊號。

### 4.2 SMA 偏離與 RSI(2) 可能是重複確認

兩個條件都直接描述近期價格疲弱：一個看價格相對均線的位置，一個看短期下跌動能。它們不一定是兩個獨立訊息來源，因此加入兩者未必代表增加兩層獨立確認。

目前沒有在 Development 階段看到移除成交量條件的 baseline 比較，所以不能確認成交量條件是否真的增加了增量價值。

### 4.3 固定 stop、target 與持有期的環境適應性不足

規則固定使用 raw entry 的 -4% stop、+4% target 與最多 15 個完整 session。這種設計容易受到不同波動環境、跳空幅度與交易成本影響。Development 中 stress profit factor 只有 1.088，支持「經濟邊際偏薄」的警訊，但不能據此推論正式 Evaluation 的結果。

## 五、規格與實作檢查

### 已確認一致的部分

- 指標只使用當日及更早的 Close、Volume；成交量先行條件透過 shift 排除了當日成交量資訊。
- 訊號在收盤確認，下一個 XNYS session open 進場。
- stop gap、target gap、同日同時觸及時 stop-first 的處理與預先登記一致。
- 部位大小同時受可用現金與含成本 stop 風險預算限制。
- 冷卻期從 completed-position-exit 起算，持倉與訊號互斥。
- 將 2013 warmup 與 2014–2018 Development 資料合併後獨立重跑，重現 29 個訊號、29 筆交易及主要 metrics。

### 已確認的文件／實作缺陷

1. **RSI 的初始資料處理不正確。**

   預先登記只寫 `RSI(2)`，沒有說明使用 Wilder 平滑或簡單 rolling mean。程式採用 rolling mean；而在資料不足時，`loss` 的 NaN 會被條件式當成「沒有損失」，使 RSI 初始值變成 100，而不是保持未就緒。這不會在本次 Development 直接製造訊號，因為成交量先行條件更晚才有效，但會影響邊界行為與未來變體的可重現性。

2. **有效 warmup 比規格寫的 20 個 session 更長。**

   20 日成交量平均量再加上前 5 日的先行窗口，完整的 `prior_volume_spike_ratio` 要到第 26 個資料列才可用，也就是需要約 25 個歷史 session。程式的 fold warmup 參數仍是 20，因此 fold 開頭可能有 5 個資料列因指標尚未就緒而被無聲跳過。Development 使用完整 2013 年 warmup，沒有因此改變本次主要數據，但規格應明確定義「warmup 完成」與「第一個可交易訊號日」。

3. **資料 provenance 路徑有版本錯置。**

   `data-snapshot-acquisition.yml` 的 `repository_root_relative_prefix` 指向 `research/tsm-mean-reversion-volume-leads--v001`，但本 Study 與實際 Development／warmup 路徑都是 `...--v002`。此外，下列兩個允許的證據檔不存在：

   - `evidence/provenance.yml`
   - `evidence/selection-evidence.yml`

   已核對的 snapshot、source code 與 manifest digest 相符，因此這是審計與可重現性缺陷，不是目前可確認的 Development 資料污染。

### 測試覆蓋缺口

測試已涵蓋成交量先行、當日成交量不影響訊號、風險部位、下一個 open 進場與基本成本比較，但沒有直接測試：

- RSI 資料不足時的 readiness 與公式邊界；
- 20／25 session warmup 邊界；
- stop gap、target gap 及同日 stop-first；
- 15-session time exit 的 off-by-one；
- 冷卻期起點與 fold reset；
- 訊號結束日期與最後可完成交易日。

本次環境沒有安裝 `pytest`，因此沒有用 test runner 執行測試；上述判斷來自程式與測試檔靜態檢查，以及獨立的 Development 重算。

## 六、下一輪調整優先順序

### 1. 規格／實作缺陷：先修可重現性

- 明確登記 RSI 的完整公式、平滑方式、`min_periods`、零 gain／loss 行為。
- 將有效 warmup 明確定為 25 個 session，或明確接受前 5 個訊號列不可交易。
- 修正 acquisition manifest 的 v001／v002 路徑，補回 provenance 與 selection evidence。
- 增加上述邊界測試。

驗收方式：獨立實作能產生完全相同的訊號日期、交易日期、出場原因與部位大小，且 digest chain 沒有缺檔或版本歧義。

### 2. Development 警訊：驗證成交量條件的增量價值

下一輪應預先登記並在 Development 階段比較相同執行規則下的 SMA／RSI baseline 與 volume-lead candidate，並保留逐年留一與 block bootstrap gate。重點是確認策略不是只靠 2015 年的特定環境取得正報酬。

### 3. 未驗證設計假說：限制性測試成交量的時效與方向

只選一個明確、預先登記的變體，例如縮短異常成交量有效窗口，或加入明確的價格方向確認；不要在本 Study 事後擴張參數網格。驗收需同時看 base、stress、年度穩健度與成本敏感度。

### 4. 未驗證設計假說：檢查固定出場規則的波動適應性

若要調整 stop／target 或持有期，應建立一個有限且事前登記的波動標準化版本，並保留較高成本與跳空情境的驗收。不能把「改用波動調整後可能更好」當成已證明結論。

## 七、不能由本次盲檢討得出的結論

- 不能判斷正式 Evaluation 是否通過或失敗。
- 不能判斷正式 Evaluation 的任何年度表現、交易、指標或失敗 gate。
- 不能宣稱 Development 警訊就是正式 Evaluation 的失敗原因。
- 不能保證上述調整會改善下一輪結果。

## 八、讀取紀錄

已讀取：

- Study manifests：`manifests/preregistration.yml`、`manifests/candidate-definition.yml`、`manifests/qualification-spec.yml`、`manifests/development-trial-inputs.yml`、`manifests/source-bundle.yml`、`manifests/data-snapshot-acquisition.yml`。
- Study evidence：`evidence/development.yml`、`evidence/development-authorization.yml`。
- 策略程式：`src/trading_2026_2/tsm_mean_reversion_volume_leads.py`。
- 測試：`tests/test_tsm_mean_reversion_volume_leads.py`。
- 同名的 Development 與 warmup snapshot。
- `pyproject.toml` 與 `uv.lock` 僅作依賴／環境核對。

未讀取或未使用：Study 的 `study.yml`、README、正式 Evaluation、challenge、replay、terminal、quarantine、full snapshot、後續事件、journals、payload，以及任何外部資料。
