# tsm-mean-reversion-two-stage-volume-reversal--v003 封存式盲檢討

## 範圍與結論限制

- workflow 固定為 `strategy-forward-replication-research--v001`。
- 目標 Study：`tsm-mean-reversion-two-stage-volume-reversal--v003`。
- Development 訊號期間是 2014-01-01 至 2018-12-31；2013 年只作 warmup。
- 本文是只根據研究設計、凍結程式、測試與 Development evidence 的 blind review。沒有讀取或使用正式 Historical Evaluation、quarantine、replay 或 Terminal 結果，也不推測正式 Evaluation 為何可能成功或失敗。

## 實際問題與影響

最重要的問題不是目前 Development gate 沒有通過；相反地，Development 摘要與交易明細都顯示它通過了預先登記的門檻。但證據量剛好停在最低線：候選只有 20 筆完成交易，且 2017 年只有 2 筆。Stress PnL 中 2018 年 4 筆交易貢獻 8,172.85，約佔總 Stress PnL 的 54.83%。這表示目前的正報酬結論仍可能高度依賴少數年份與少數事件，不能把「五個 signal 年都有正報酬」誤解成已經有五個同等充分的獨立樣本。

另外，baseline 同時拿掉「成交量先行」和「訊號日收紅」兩個條件。候選在 Stress 比 baseline 多 4.88 個百分點報酬，但這個比較不能說明改善是由成交量條件、價格方向條件，還是兩者交互作用造成。當前研究因此能支持「整組更嚴格的篩選器在 Development 表現較好」，不能支持完整的「量先換手＋價行止跌」機制已被單獨驗證。

最後，程式雖然有處理 stop gap，但 Development 的 20 筆交易中有 7 筆 `target-gap`、5 筆普通 `stop`，沒有 `stop-gap` 或 `stop-same-session`。目前的 2% 風險預算是按正常 stop 和成本計算；遇到低於 stop 的開盤跳空時，實際損失仍可能超過這個預算。這不是已知的 Evaluation 失敗原因，而是目前 Development 尚未充分施壓的設計風險。

## 規格與實作檢查

### 已核對一致的部分

- `mean_reversion_gap >= 0.015`、RSI 上限 50、訊號日前 5 個 session 的成交量先行條件，以及收盤高於前一收盤的條件，均在程式中以當日及更早資料計算。
- 成交量先行條件透過 `shift(1)` 和過去 5 個 ratio 的 rolling max 實作，當日成交量不會偷用於當日訊號；測試也覆蓋了這點。
- 訊號在收盤後接受，下一個 XNYS session open 進場；持倉互斥、退出後 5 個 session 才可重新接受訊號，與 preregistration 一致。
- 進出場滑價、費用、raw entry 的 4% stop/target、gap at open，以及同日同時觸及時 stop-first，均有對應實作與測試。
- 可用現金上限、不借款、單一部位、整數股，以及把進出場成本納入正常 stop 風險預算，均有實作。
- `strategy_engine_digest` 與凍結的 Source Bundle 對得上；本次未發現已能確認的 look-ahead、cooldown 起點或持有期 off-by-one 錯誤。

### 已確認的規格缺口

1. preregistration 只寫「RSI(2)」，沒有固定 Wilder RSI、簡單 rolling mean 或其他算法。現行程式實際採用簡單 rolling mean，測試驗證的是這個選擇，但不是驗證它已被 preregistration 明確指定。下一輪若不把 RSI 公式寫死，同一個參數名稱仍可能產生不同訊號。
2. 成交量條件只登記 20 日平均與 5 日窗口，沒有明確寫出平均值是否排除當日、5 日窗口的邊界及 ratio 的計算基準。現行程式採「前 20 個 session 的平均量」再取前 5 個 ratio 的最大值；這個實作合理且沒有看到未來資料，但可重現性仍依賴程式細節。

這兩項是規格可重現性缺陷，不應在本 Study 內回寫修補；應在新 Study 的 preregistration、candidate definition、fixture 測試中一併固定。

## Development 穩健度

我從 Development 的 20 筆交易明細重新加總 PnL、profit factor、equity path 與最大回撤，結果與 evidence 摘要一致：

| 指標 | Base | Stress |
|---|---:|---:|
| 完成交易 | 20 | 20 |
| 勝／負筆數 | 13／7 | 13／7 |
| 報酬 | 19.76% | 14.90% |
| Profit factor | 2.760 | 2.315 |
| 最大回撤 | 3.96% | 4.34% |
| 最大單筆已實現虧損／進場前資金 | 2.00% | 2.00% |
| 最長連敗 | 2 | 2 |

已記錄的 50,000 次 block bootstrap 顯示，Stress 正報酬比例在 block length 3／5 分別為 97.57%／97.13%，回撤超過 10% 的比例為 0.374%／0.600%。Leave-one-signal-year-out 的最差 Stress 結果仍是報酬 6.73%、profit factor 1.594、最大回撤 4.34%。這些數字支持「Development 內的交易順序不是只靠單一被移除年份才成立」，但它們仍只是在 20 筆交易上重抽樣，不能替代更多獨立市場階段。

按 signal year 的 Stress PnL 如下：

| 年份 | 交易數 | Stress PnL | 佔總 Stress PnL |
|---|---:|---:|---:|
| 2014 | 5 | 1,170.65 | 7.85% |
| 2015 | 5 | 3,253.57 | 21.83% |
| 2016 | 4 | 1,251.19 | 8.39% |
| 2017 | 2 | 1,056.32 | 7.09% |
| 2018 | 4 | 8,172.85 | 54.83% |

退出型態是 7 筆 target-gap、6 筆 target、5 筆 stop、2 筆 time。這說明成本與獲利跳空路徑有被看到，但虧損跳空和同日 stop-first 路徑尚未在 Development 交易中實際出現。

## 調整優先順序

1. **規格／實作缺陷：固定 RSI 與成交量 ratio 的完整算法。** 預期解決不同實作者對同一訊號產生不同交易的問題。副作用是訊號數可能改變，不能直接把新算法套回本 Study。驗收方式：新 Study 的 manifest 明確寫出公式、資料邊界與 ready index，並用人工可算的 synthetic fixture 同時驗證策略程式與 runner。
2. **未驗證設計假說：拆開兩個新增篩選條件的增量效果。** 下一輪應事先固定有限的 volume-only、price-direction-only 或等價的因素拆解，並事先處理完整 family 的多重比較。驗收方式是比較各預先指定變體的交易數、跨年份結果、成本敏感度與樣本集中度；不能只挑表現最好的拆解。副作用是候選家族變大、統計門檻會更嚴格。
3. **Development 警訊：處理最低樣本量與年份集中。** 目前候選剛好 20 筆，且 2018 貢獻過半 Stress PnL。下一輪應事先指定每個年份的最低資訊量、較長的 Development 區間，或獨立的時間區塊驗證；不要事後降低門檻來保留候選。驗收方式是正報酬不再主要由單一年份或單一大獲利事件提供。
4. **未驗證設計假說：對 adverse stop gap 做有限、預先登記的壓力測試。** 目標是確認「2% 正常 stop 風險預算」在開盤跳空時仍符合可接受的單筆損失上限。驗收方式應明確定義 gap 情境、成本與最差成交規則，並要求最大單筆損失與回撤 gate；副作用是可能淘汰只在平順成交假設下有效的策略。

## 不能得出的結論

本次不能判斷正式 Historical Evaluation 是否通過，也不能判斷任何正式失敗的原因。Development pass、bootstrap 與 leave-one-year-out 只說明在已開放的 2014–2018 資料上，候選符合預先登記的 Development gates；它們不保證上述調整能改善正式結果。

## 讀取紀錄

本次實際讀取：

- 盲檢討技能與方法：`.agents/skills/blind-review-strategy-study/SKILL.md`、`.agents/skills/blind-review-strategy-study/references/review-method.md`。
- Study manifests：`manifests/preregistration.yml`、`manifests/candidate-definition.yml`、`manifests/qualification-spec.yml`、`manifests/development-trial-inputs.yml`、`manifests/source-bundle.yml`、`manifests/data-snapshot-acquisition.yml`。
- Study Development evidence：`evidence/development.yml`、`evidence/development-authorization.yml`、`evidence/provenance.yml`、`evidence/selection-evidence.yml`。
- Source Bundle 允許的 repository 檔案：`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v003.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v003.py`、`pyproject.toml`、`uv.lock`（僅檢查檔案行數，未使用其內容）。

本次沒有讀取 Study 的 `study.yml`、任何 Historical Evaluation／Terminal evidence、後段 events、journals、terminal/evaluation payload、full/quarantine/historical-evaluation 原始價格資料，也沒有使用網路、broker、外部市場資料或 connector。Review 檔本身是補充性的封存筆記，不是 stage evidence、candidate、event、terminal evidence 或 outcome。
