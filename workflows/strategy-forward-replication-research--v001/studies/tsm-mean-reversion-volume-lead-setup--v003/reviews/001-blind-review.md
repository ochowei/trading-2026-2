# 封存式 Study 檢討報告：tsm-mean-reversion-volume-lead-setup--v003

## 1. 範圍與結論限制

- **研究工作流程**：`strategy-forward-replication-research--v001`
- **檢討目標 Study**：`tsm-mean-reversion-volume-lead-setup--v003`
- **檢討性質**：封存式盲檢討（Blind Review）。
- **分析範圍**：僅使用研究設計規格、候選定義、策略程式碼與 2013 暖機（warmup）及 2014–2018 開發期（Development）證據。
- **結論限制**：本檢討完全未開啟、未讀取、亦未參考 2020–2024 正式歷史評估（Historical Evaluation）、九項穩健度挑戰（Robustness Challenges）、回放測試（Replay）或最終結果（Terminal Evidence）。本報告不對正式評估結果進行任何推測或歸因。

---

## 2. 實際問題與影響（白話解析）

這個策略的核心構想是：當台積電（TSM）短線跌深（股價比 20 日均線低 2% 以上、且 2 日 RSI 處於超賣狀態 35 以下），如果「過去 5 個交易日曾出現異常大成交量（超過 20 日均量的 1.25 倍）」，就認為市場已有買盤積極介入，即使**訊號當天股價還在下跌破底、完全沒有收紅反轉**，也直接在隔天開盤進場做多。

這個設計在實際交易中產生了以下嚴重問題與影響：

1. **把「爆量下跌」誤當作「止跌訊號」，形同接落下的飛刀**：
   在股價跌勢中，成交量突然放大往往代表「停損賣壓出籠」或「主力大舉出貨」，並不代表價格已經見底。取消了原本「訊號日必須收高於前一日」的止跌確認門檻後，策略經常在恐慌重挫的半途中接刀，導致進場後立即被後續跌勢觸發停損出場。
2. **加入爆量條件後，績效反而顯著落後於最簡單的基準策略（Baseline）**：
   相同資金與風控下，完全不看成交量、單純逢低買進的 SMA＋RSI 基準策略，在開發期繳出 22.95% 的報酬率；但本候選策略加上「前 5 天爆量」條件後，報酬率直接驟降到 6.86%（壓力成本下只剩 2.03%），等於為了這個未經充分驗證的量價假設，白白損失了超過 16% 的潛在獲利。
3. **過度依賴 2015 單一年度，其餘年份整體虧損**：
   在開發期 5 年（2014–2018）共 29 筆交易中，光 2015 年就有 11 筆交易且貢獻了全部的獲利。如果把 2015 年扣除，其餘 4 個年份合併起來是實質虧損的。

---

## 3. 規格與實作檢查

經對照 `manifests/preregistration.yml`、`manifests/candidate-definition.yml` 與程式原始碼 `src/trading_2026_2/tsm_mean_reversion_volume_lead_setup_v003.py` 及核心模組：

### (1) 已確認缺陷（實作程式錯誤）
- **無重大程式缺陷**：
  程式碼指標計算（SMA 20、RSI 2、成交量移動均線）、信號產生邏輯、開盤委託模擬、GTC 停損與 DAY 停利掛單、以及成本滑價計算法，均與預先登記（Preregistration）內容完全一致。
  單元測試 `tests/test_tsm_mean_reversion_volume_lead_setup_v003.py` 亦正確覆蓋了本版本「不要求訊號日收紅」的行為特徵。

### (2) 純設計風險（經濟假說與交易邏輯漏洞）
- **Setup（環境條件）與 Trigger（進場觸發）角色混淆**：
  均線乖離與成交量放大只能界定「潛在的反轉環境（Setup）」，不能代替「買方已扭轉跌勢的實際動作（Trigger）」。移除訊號日收紅確認後，策略喪失了最基本的價格確認保護。
- **摩擦成本脆弱度極高**：
  在 Base 成本（單邊 1 bps 手續費 + 5 bps 滑價）下，策略獲利為 $6,858.99；但在 Stress 成本（單邊 2 bps 手續費 + 20 bps 滑價）下，獲利腰斬至 $2,027.67。超過 70% 的利潤被交易摩擦吃掉，容錯空間（Margin of Safety）極度狹窄。

---

## 4. Development 穩健度與重算數據

本 Study 在開發期即已被判定為 **不合格（fail）**，共有 4 項 Development Gates 未通過：

| 評估項目 / 門檻名稱 | 預先登記要求 | 實際數值 | 判定結果 |
| :--- | :--- | :--- | :--- |
| **基礎報酬率 (Base Return)** | > 0 | +6.86% | 通過 |
| **基礎獲利因子 (Base Profit Factor)** | > 1.10 | 1.29 | 通過 |
| **完成交易筆數 (Completed Trades)** | >= 20 | 29 筆 | 通過 |
| **交易涵蓋年份 (Traded Years)** | >= 3 年 | 5 年 | 通過 |
| **單筆最大虧損比例** | <= 4.00% | 2.30% | 通過 |
| **壓力測試最大回撤 (Stress MDD)** | <= 10.00% | 6.77% | 通過 |
| **壓力測試獲利因子 (Stress PF)** | > 1.00 | 1.09 | 通過 |
| **壓力測試報酬率 (Stress Return)** | > 0 | +2.03% | 通過 |
| **區塊抽樣回撤超標比例 (Bootstrap DD > 10%)** | **<= 10.00%** | **25.01%** | **失敗 (FAIL)** |
| **區塊抽樣正報酬比例 (Bootstrap Positive Return)** | **>= 80.00%** | **60.00%** | **失敗 (FAIL)** |
| **留一年度驗證最小 PF (Leave-One-Year-Out PF)** | **> 1.00** | **0.9675** | **失敗 (FAIL)** |
| **留一年度驗證最小報酬 (Leave-One-Year-Out Return)** | **> 0** | **-0.46%** | **失敗 (FAIL)** |

### 年度分段盈虧分佈（Stress 條件）
- **2014 年**：3 筆交易，損益 -$1,103.74
- **2015 年**：11 筆交易，損益 **+$2,470.39**（獲利高度集中）
- **2016 年**：5 筆交易，損益 -$1,010.13
- **2017 年**：3 筆交易，損益 +$647.34
- **2018 年**：7 筆交易，損益 +$1,023.80
- **排除 2015 年後的剩餘 4 年合計損益**：**-$442.72**（轉為實質淨虧損）

---

## 5. 調整建議分級

### A. 規格／實作缺陷
- **無**：目前程式無實作偏離規格問題。

### B. Development 警訊（由開發期數據支持）
1. **必須正視策略嚴重落後於 Baseline 的事實**：
   在相同的 15 天持有期與 4% 停損停利機制下，完全不篩成交量的 Baseline 策略淨報酬為 22.95%，而加上成交量前置條件後降至 6.86%。下一輪研究應評估「成交量前置條件」是否本身即為無效濾網。
2. **解決極端的年度依賴性**：
   2015 年以外的整體虧損，證明該策略在震盪或不同市場環境下的泛化能力不足，不能單看全期總和為正就認為可行。

### C. 未驗證設計假說（需於新 Study 預先登記並驗證）
1. **重新納入價格反轉觸發機制（Trigger）**：
   假說：「在跌深且爆量的環境下，必須同時伴隨價格止跌訊號（例如訊號日當天收盤站回前日收盤之上，或當日收長下影線），才能有效過濾順勢崩跌的假突破」。
2. **重新檢視成交量倍數與時間窗口**：
   過去 5 天出現 1.25 倍均量的條件可能過於寬鬆且時間落差過大（5 天前的量對當下進場已無引導作用）。可驗證將窗口縮短至 1–2 天，或提高爆量門檻。

---

## 6. 不能得出的結論

1. **不得推論正式 Evaluation 的結果**：
   本檢討完全不知悉、亦未檢視 2020–2024 年正式評估的結果。我們不能宣稱正式評估是因為上述原因而失敗，也不能宣稱策略在正式評估中有無通過。
2. **不保證調整後必然能通過正式評估**：
   上述建議僅基於 2014–2018 開發期數據與交易經濟學邏輯推導，未來的市場微觀結構可能已產生變化，所有調整均須嚴格建立新 Study 重新預先登記與獨立驗證。

---

## 7. 檔案讀取紀錄與聲明

### 本次實際讀取之檔案清單
1. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-lead-setup--v003/manifests/preregistration.yml`
2. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-lead-setup--v003/manifests/candidate-definition.yml`
3. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-lead-setup--v003/manifests/qualification-spec.yml`
4. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-lead-setup--v003/manifests/source-bundle.yml`
5. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-lead-setup--v003/manifests/data-snapshot-acquisition.yml`（僅檢閱元資料結構）
6. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-lead-setup--v003/manifests/development-trial-inputs.yml`
7. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-lead-setup--v003/evidence/development.yml`
8. `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-lead-setup--v003/evidence/development-authorization.yml`
9. `src/trading_2026_2/tsm_mean_reversion_volume_lead_setup_v003.py`
10. `src/trading_2026_2/tsm_mean_reversion_reversal_trigger_v001.py`
11. `tests/test_tsm_mean_reversion_volume_lead_setup_v003.py`
12. `research/tsm-mean-reversion-volume-lead-setup--v003/run_development.py`

### 聲明
本次檢討嚴格遵守盲檢討讀取規範，**完全沒有讀取或使用**目標 Study 的 `study.yml`、`README.md`、`evidence/terminal-evidence.yml`、`evidence/historical-evaluation*`、`events/000008-*`、`journals/` 或任何 2019 年後的市場價格資料與評估結果。
