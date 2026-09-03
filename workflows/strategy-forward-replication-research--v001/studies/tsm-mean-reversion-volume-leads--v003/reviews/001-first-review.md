# tsm-mean-reversion-volume-leads--v003 封存式盲檢討

## 1. 範圍與結論限制

本次固定檢討 `strategy-forward-replication-research--v001` workflow 的單一 Study：
`tsm-mean-reversion-volume-leads--v003`。

可用資料角色是 2013-01-01 至 2013-12-31 的 `warmup-only`，以及 2014-01-01
至 2018-12-31 的 `development`。本次只使用研究設計、凍結候選的程式與測試、
以及 Development 證據；沒有讀取或使用正式 Evaluation、robustness challenge、
replay、terminal 結果，也沒有使用網路、券商或外部資料。因此本報告不能回答正式
Evaluation 是否通過，也不能推測正式結果的失敗原因。

## 2. 實際問題與影響

最重要的問題是：額外加入的「前五個 session 內有成交量異常」和「訊號日收盤下跌」
條件，在 Development 沒有顯示出比簡單 SMA＋RSI baseline 更好的穩健性，反而把交易
數從 40 筆減到 28 筆。候選在 base 成本下仍有正報酬，但壓力成本下只剩約 6.53 元的
淨利（起始資金 100,000 元），幾乎沒有安全邊際。

這比較像「條件挑到的情境沒有足夠增量資訊」的設計警訊，不是目前已確認的單筆交易
計算錯誤。另有兩個需要補強的可重現性問題：核心程式沒有自行驗證 XNYS session
是否連續，而且 `reset_at_start` 只延後交易、沒有在函式內重建指標狀態；若呼叫端把
前一個 fold 的資料一併傳入，就可能把前 fold 的指標歷史帶進來。本次依盲檢討白名單
沒有讀取 runner，所以不能說實際 runner 已經發生這個問題，但目前核心介面的隔離
保證不足。

## 3. 規格與實作檢查

### 已核對一致的部分

- 訊號在 session 收盤決定。程式用當日 Close 計算 SMA、RSI 和方向條件；成交量
  條件先對成交量比率做一次 shift，再取前五個 session 的最大值，所以訊號日的
  成交量不會被偷用。門檻的包含方式也與規格一致：均線偏離和成交量比率使用大於
  等於，RSI 使用小於等於，收盤方向使用嚴格小於。
- 交易在下一個 XNYS session 開盤進場；進場滑價、出場滑價、費用、gap、同一 session
  同時觸及停損與停利時停損優先，均與 candidate definition 相符。
- 停損與停利都由 raw entry open 的 -4%／+4% 計算，持有 15 個完整 session 後在下一個
  open 出場；冷卻時鐘從已完成部位的出場點開始。現有測試覆蓋了次日進場、15 個
  session 出場和五個 session 冷卻。
- 部位股數同時受可用現金和含成本的停損風險預算限制，使用最大整數股數；Development
  證據中的最大實現單筆虧損仍低於 4% gate。
- `strategy_engine_digest`、source bundle 及 target manifests 的 SHA-256 都能與
  Development trial inputs 所綁定的雜湊對上，表示本次核對的是被綁定的程式版本。

### 已確認或需要明確化的缺口

1. **規格／實作保證不足：XNYS session 沒有由核心程式驗證。**
   `validate_bars` 會檢查日期遞增、重複和 OHLCV 合法性，但不會檢查日期是否為 XNYS
   session，也不會拒絕中間缺少交易日。這次 acquisition manifest 的 Development
   快照有完整性紀錄，不能據此推論所有未來呼叫都安全。下一輪應讓 runner 或核心
   validator 對固定 XNYS session 清單做硬性檢查。

2. **規格／實作保證不足：fold 隔離依賴呼叫端。**
   `backtest(reset_at_start=True)` 會把前 25 列設為暖機，但 `indicators()` 仍先對傳入
   的整個 DataFrame 計算 rolling 指標。如果輸入包含上一個 fold 的歷史，指標狀態仍會
   延續；只有呼叫端確實只傳入「本 fold 的 25 個 warmup session＋本 fold 資料」時，
   才符合不跨 fold 帶狀態的規格。現有測試只有單一局部 frame，沒有測試前置資料造成的
   差異。

3. **規格未完整記錄：RSI 的公式。**
   程式明確使用簡單 rolling mean 的 gain/loss 計算 RSI，但可讀的 candidate manifest
   只指定 RSI 長度和門檻，沒有把這個公式寫成規格。這不是由現有證據確認的錯算，
   卻會讓「RSI(2)」在另一個實作者手上產生不同訊號。下一輪應明定公式、暖機邊界和
   零 gain／零 loss 的處理。

4. **規格未完整記錄：成交量先行的分母與事件語意。**
   程式把每個過去 session 的成交量，除以前 20 個 session 的平均成交量，再取訊號
   前五個 session 的最大比率。這符合「前五日曾有異常量」的一種明確解讀，但規格沒有
   清楚寫出是逐日 rolling ratio、是否允許多次異常、以及異常量本身是否需要與下跌同向。
   因此不能把這個條件當作已驗證的「量先於價」因果訊號。

5. **設計風險：方向確認比較像延續弱勢，而不是反轉 trigger。**
   訊號要求當日收盤低於前一日，然後下一個 open 直接做多；在進場前沒有要求價格先
   止跌或出現反轉。這可能把均值回歸 setup 和仍在下跌的 falling-knife 情境混在一起。
   這是合理但未驗證的機制推論，不是正式 Evaluation 的失敗原因。

6. **測試覆蓋仍不足。**
   已有測試涵蓋指標暖機、先前成交量、baseline 開關、風險股數、gap／同日觸發、
   進出場和冷卻；但沒有覆蓋 XNYS 假日／缺 session、`signal_start`／`signal_end` 的
   完整生命週期、含前一 fold 歷史的 reset、零股數訊號，以及時間出場與成本的邊界。

## 4. Development 穩健度

我從允許的逐筆 Development trade ledger 重新彙總候選數字；結果與 evidence 摘要
一致。baseline 只有 aggregate 統計，因此 baseline 部分採用 evidence 中已記錄的
彙總值。

| 指標 | 候選 base | 候選 stress | 簡單 baseline base | 簡單 baseline stress |
|---|---:|---:|---:|---:|
| 完成交易 | 28 | 28 | 40 | 40 |
| 報酬 | 4.4229% | 0.0065% | 22.9549% | 14.4157% |
| Profit factor | 1.1913 | 1.0003 | 1.7130 | 1.4680 |
| 最大回撤 | 6.4030% | 8.0878% | 6.7006% | 6.7679% |
| 交易年度 | 5 | 5 | 5 | 5 |

候選相對 baseline 的報酬差為 base -18.532 個百分點、stress -14.409 個百分點。
候選的 28 筆交易中，停損類 10 筆、停利類 12 筆、時間出場 6 筆；stress 下六筆
時間出場合計約 -575.54 元。這與 stress 總毛利約 22,894.75 元、總毛損約
22,888.22 元相抵後只剩 6.53 元的結果相符。最大單筆已實現虧損比例為 base 2.2954%、
stress 2.2736%，所以目前最明顯的問題是整體 edge 太薄，不是單筆風險 gate 超標。

### 按 signal 年度

| Signal 年度 | 交易數 | Base PnL | Stress PnL |
|---|---:|---:|---:|
| 2014 | 3 | -726.84 | -1,103.71 |
| 2015 | 11 | 4,413.04 | 2,470.42 |
| 2016 | 4 | -2,492.62 | -2,833.65 |
| 2017 | 3 | 1,175.97 | 636.42 |
| 2018 | 7 | 2,053.40 | 837.05 |

Stress leave-one-signal-year-out 的結果如下；每一列都是移除該年度後重新計算。

| 移除年度 | 剩餘交易數 | Profit factor | 報酬 | 最大回撤 |
|---|---:|---:|---:|---:|
| 2014 | 25 | 1.0532 | 1.1226% | 8.0877% |
| 2015 | 17 | 0.8258 | -2.4307% | 7.0448% |
| 2016 | 24 | 1.1539 | 2.8826% | 6.7672% |
| 2017 | 25 | 0.9695 | -0.6353% | 8.6776% |
| 2018 | 21 | 0.9512 | -0.8305% | 6.7672% |

移除 2015 年時 stress 報酬變負且 profit factor 低於 1；移除 2017 或 2018 年也變負。
這表示五個 signal 年度並不是五個都支持同一個效果。Base 移除 2015 年後也只剩
-0.0215% 報酬、0.9985 profit factor，雖然這不是本 Study 的 stress gate，仍是同方向
的穩健度警訊。

### Block bootstrap

既有 50,000 次、固定 seed 的 block bootstrap 也不支持「壓力成本下大多數路徑都能
獲利」：

| Stress block 長度 | 正報酬比例 | 最大回撤超過 10% 比例 | 報酬 q05／q50／q95 | Profit factor q50 |
|---:|---:|---:|---:|---:|
| 3 | 50.224% | 34.794% | -13.208%／0.047%／14.915% | 1.0020 |
| 5 | 50.444% | 27.364% | -11.248%／0.071%／12.323% | 1.0031 |

Development evidence 記錄的四個失敗 gate 是：

- stress block bootstrap 中最大回撤超過 10% 的比例；
- stress block bootstrap 正報酬比例；
- stress leave-one-year-out 的最低 profit factor；
- stress leave-one-year-out 的最低報酬。

這些是 Development 證據支持的結論，不代表正式 Evaluation 的結果。

## 5. 調整優先順序

### P0：先修正可重現性邊界（規格／實作缺陷）

讓資料入口硬性驗證 XNYS session、缺漏日期和 fold-local warmup；並讓 fold reset
真正保證 rolling 指標不使用前 fold 歷史。驗收方式是：注入週末、假日或缺列時明確
拒絕；把同一 fold 接在一段前置歷史後執行，結果必須與只含本 fold warmup 的執行
完全相同。副作用是會更早拒絕格式看似正常但 session 不完整的資料。

### P1：把「優於簡單 baseline」當成真正的增量問題（Development 警訊）

下一輪不要只看候選是否剛好大於零；應在預先登記時明確寫出候選要解決 baseline 的
哪個缺點，以及在相同執行、成本和風險下要達到什麼 incremental gate。不能把本 Study
的 Development 結果拿來事後調參。副作用是可能淘汰報酬為正、但沒有證明額外條件有
用的策略。

### P2：只預先登記一個反轉 trigger 假說（未驗證設計假說）

下一輪可把「收盤低於前收」改成一個明確的止跌／反轉條件，或先保留現行條件作為
直接否證對照；兩者只能擇一，不能在同一 Development 窗口擴張參數網格。驗收應包括
既有 stress、leave-one-year-out 和 block bootstrap gate，並要求相對 baseline 有
預先指定的增量改善。可能副作用是訊號更少、進場更晚、成本更高。

### P3：把成交量先行改寫成可否證的單一定義（未驗證設計假說）

明確指定異常量的 rolling 分母、五日窗口如何判定、以及是否需要與下跌同向；只測一個
事前寫好的定義。若仍無法在同一執行規則下提供相對 baseline 的增量穩健性，就應移除
這個 filter，而不是繼續微調 1.15／1.25／1.35 等門檻。可能副作用是交易數下降或
失去原本想捕捉的事件型訊號。

### P4：提早暴露成本脆弱性（Development 警訊）

把壓力成本的最低安全邊際與時間出場的成本敏感度放進下一輪的早期判定，且在看資料前
固定門檻；不要讓「stress 報酬剛好大於零」被當成實質優勢。這會增加否證率，但能
避免把幾乎沒有成本餘裕的候選送進後續階段。

## 6. 不能得出的結論

本次不能判斷正式 Evaluation、challenge、replay 或 terminal 的通過／失敗，也不能
把 Development 的四個 failed gates 當成正式結果的失敗原因。以上調整是下一輪可
預先登記的有限假說和工程驗收條件，不保證任何正式結果一定改善。

## 7. 讀取紀錄

### 實際讀取或雜湊核對

- `.agents/skills/blind-review-strategy-study/SKILL.md`
- `.agents/skills/blind-review-strategy-study/references/review-method.md`
- `workflows/strategy-forward-replication-research--v001/workflow.yml`
- `workflows/strategy-forward-replication-research--v001/rules/evidence-requirements.yml`
- `workflows/strategy-forward-replication-research--v001/rules/state-machine.yml`
- `workflows/strategy-forward-replication-research--v001/rules/workflow-floors.yml`
- 目標 Study 的 `manifests/preregistration.yml`
- 目標 Study 的 `manifests/candidate-definition.yml`
- 目標 Study 的 `manifests/qualification-spec.yml`
- 目標 Study 的 `manifests/development-trial-inputs.yml`
- 目標 Study 的 `manifests/source-bundle.yml`
- 目標 Study 的 `manifests/data-snapshot-acquisition.yml`
- 目標 Study 的 `evidence/development.yml`
- 目標 Study 的 `evidence/development-authorization.yml`
- `research/tsm-mean-reversion-volume-leads--v003/data/snapshots/TSM-warmup-only--sha256-f1b8995472c52e09a8053b814def83beeaa15257da7cded2d882f576293dae11.csv`
- `research/tsm-mean-reversion-volume-leads--v003/data/snapshots/TSM-development--sha256-6cdc27048ccbe39ba5d1054152d668bb1423d8d5075ce99548d04b314541bc79.csv`
- `src/trading_2026_2/tsm_mean_reversion_volume_leads_v003.py`
- `tests/test_tsm_mean_reversion_volume_leads_v003.py`
- `pyproject.toml`
- `uv.lock`（只做 source bundle 雜湊核對）

### 檢查但不存在的檔案

- `evidence/provenance.yml`
- `evidence/selection-evidence.yml`

因此本次無法獨立核對這兩份 provenance／候選選擇證據；沒有用其他 Study、複製資料或
禁止的後段 evidence 來補足。

### 明確沒有讀取或使用

沒有讀取 `study.yml`、Study 或 research 的 README、正式 Evaluation／quarantine／
retrospective-replay 價格快照、`evidence/historical-evaluation*`、terminal／challenge／
replay payload、後續事件、journals，也沒有讀取或執行 Development runner 或任何
後段結果程式。正式 Evaluation、robustness challenge、replay、terminal 結果在本次
盲檢討中均未讀取、未使用。
