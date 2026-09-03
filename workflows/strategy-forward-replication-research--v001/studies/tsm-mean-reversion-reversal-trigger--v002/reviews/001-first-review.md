# tsm-mean-reversion-reversal-trigger--v002：第 001 次封存式盲檢討

## 1. 範圍與結論限制

本檔是 `strategy-forward-replication-research--v001` 的補充性盲檢討筆記，不是 stage evidence、candidate、event、outcome 或 terminal evidence。目標 Study 為 `tsm-mean-reversion-reversal-trigger--v002`。

本次只使用 preregistration、candidate/development inputs、Development evidence、source bundle 指向的策略程式與測試。Development 的訊號期間是 2014-01-01 至 2018-12-31，2013 年只作 warmup。沒有回答、也不推測正式 Evaluation 的表現或失敗原因。

Study 內下列白名單檔案缺失，因此無法獨立核對資料取得角色、資格規格、provenance 與 candidate selection 的完整鏈結：`manifests/qualification-spec.yml`、`manifests/data-snapshot-acquisition.yml`、`evidence/provenance.yml`、`evidence/selection-evidence.yml`。不以 source bundle 列出的 `research/` 副本補讀。

## 2. 實際問題與影響

最重要的問題是候選過度稀疏：Development 只有 13 筆完成交易，低於預先登記的 20 筆門檻，因此 Development gate 已失敗。五個訊號年度只有 2 至 4 筆交易；此時較高的 profit factor 和較低的回撤，還不足以支撐「反轉觸發條件帶來穩健性」的強結論。

候選相對簡單 baseline 的取捨也很明顯：候選 13 筆交易，baseline 40 筆；候選 base/stress 報酬為 9.85%/7.11%，baseline 為 22.95%/14.42%。候選的 profit factor 與最大回撤較好，但交易數只保留 32.5%，報酬也較低。這種改善可能部分來自少做交易、少承受成本與風險，而不一定是新增條件本身提高了每個市場環境的預測力。

獲利也有時間集中：由交易明細重算，2016--2018 貢獻候選 gross positive PnL 的 base 65.9%、stress 65.8%；2014--2015 合計為負。leave-one-year-out 雖然每次刪掉一年後仍為正，但剩下只有 9--11 筆交易，且沒有檢驗連續的 regime 轉換。這是 Development 警訊，不是正式 Evaluation 失敗原因。

## 3. 規格與實作檢查

### 已核對一致的部分

- 訊號只使用當日及以前資料：成交量異常取訊號日前 5 個 session，收盤方向是 `Close > prior Close`；測試也確認改動訊號日當日 Volume 不會改變訊號。訊號在收盤確認，下一個 session open 才進場。
- 冷卻從 completed-position exit 起算，持有 15 個完整 session；程式與測試對 next-open、15-session time exit、五個 session cooldown 及 25-session warmup 有直接核對。
- 停損、停利、gap fill、同日同時觸發時 stop-first，以及含成本的整數股風險預算，均與 candidate definition 的主要執行規則相符。

### 已確認的規格／實作防護缺口

1. Candidate 宣告使用 XNYS 與 America/New_York，但 `validate_bars` 只檢查日期型別、排序與重複，沒有驗證日期是否為 XNYS session；回測又以輸入列數計算持有期與 cooldown。若輸入漏掉假日或混入非交易日，session 計數就會改變。對帶時區 index，程式直接移除時區，沒有先轉成 America/New_York。這不能證明本次 Development 已受影響，但下一輪應把日曆與時區變成明確的輸入契約並加測試。
2. Preregistration 只寫 `RSI(2)`，沒有指定 RSI 公式；程式實作的是 gain/loss 的簡單 rolling mean。這是可重現性缺口，不足以直接判定本次程式錯誤。下一輪應把公式、min-periods 與零 gain/loss 的邊界寫入 qualification spec。
3. 程式的 `maximum_drawdown` 是依完成交易的 PnL 序列計算；若規格原意包含持倉內的價格路徑或 gap 期間，現在的指標定義不夠清楚。因 qualification spec 缺失，本項只能列為未完成的規格核對，不能宣稱 gate 計算錯誤。

測試涵蓋指標就緒、先前成交量、風險股數、gap/stop-first、進出場、cooldown、warmup 與 synthetic runner schema；但沒有覆蓋 XNYS 缺 session、時區轉換、signal start/end 邊界、持倉內 drawdown 定義，或實際跨 fold 的資料狀態隔離。

## 4. Development 穩健度

以下數字先由 `evidence/development.yml` 的 13 筆交易明細重算，再與 evidence 摘要核對：

| 指標 | Base | Stress |
|---|---:|---:|
| 完成交易 | 13 | 13 |
| 報酬 | 9.85% | 7.11% |
| Profit factor | 2.496 | 2.044 |
| 最大回撤 | 2.15% | 2.42% |
| 最大實現單筆虧損占比 | 2.00% | 2.00% |
| 獲利交易比例 | 8/13（61.5%） | 8/13（61.5%） |
| 最長連續虧損 | 1 筆 | 1 筆 |

出場原因為 target 5 筆、target-gap 3 筆、stop 3 筆、time 2 筆；沒有觀察到 stop-gap 或 stop-same-session。這個交易路徑很平滑，但樣本太小，不能把「沒有連續虧損」當成未來風險已被排除。

既有 Development diagnostics 顯示：

- leave-one-year-out 的 stress 報酬範圍為 2.99%--8.03%，profit factor 為 1.450--3.856，最大回撤不超過 2.42%；但每次只剩 9--11 筆交易。
- 50,000 次 block bootstrap 的 stress 結果，block length 3/5 的正報酬比例為 96.562%/99.02%，報酬第 5 百分位為 0.619%/2.654%，最大回撤第 95 百分位為 4.52%/4.37%。這些是 evidence 已保存的摘要；它們重抽的是同一批 13 筆交易，沒有新增未觀察市場狀態，因此不能取代更多年度或連續區段驗證。

## 5. 調整優先順序

### A. 規格／實作缺陷：先修正

1. 補齊 qualification、data acquisition、provenance、selection evidence，並讓資料角色、日期界線、程式 digest 與 Development evidence 可互相核對。
2. 明確定義 RSI 公式、指標就緒規則與 maximum drawdown 是交易結束後的 realized equity，還是包含持倉內 mark-to-market；用固定 fixture 測試。
3. 明確驗證 XNYS session 與 America/New_York 時區，並測試缺一個假日、帶 UTC index、cooldown 邊界及 signal end 後完整交易生命週期。若驗證由上游 runner 負責，則應在契約中明確標示，不能只靠呼叫者默認。

### B. Development 警訊：下一輪驗收

不要為了讓 gate 通過而事後放寬門檻。下一輪應預先登記一個有限的增加樣本方案，並仍要求至少 20 筆完成交易、至少 3 個訊號年度；同時保留候選與 baseline 的相同成本比較。對 2014--2018 這種年度集中，應加入預先指定的連續區段或 rolling-period 檢查，不能只依 leave-one-year-out 與 trade-level bootstrap。

### C. 未驗證設計假說：只能放入新 Study

優先驗證兩個附加條件是否真的各自有用：把「先前成交量異常」與「訊號日收盤上升」做成事先登記的有限 ablation family，並對完整 family 做多重比較調整；不要事後展開更大的參數網格。其次才驗證固定 ±4% stop/target 與 15-session holding period 是否在不同波動狀態仍合理。這些是待驗證假說，不是本次 Study 可回寫的修正結果。

## 6. 不能得出的結論

本次不能判斷正式 Evaluation、robustness challenge、replay 或 terminal review 是否通過，也不能說它們若失敗是由上述任何設計弱點造成。上述建議只能改善下一輪的可辨識性與驗證力，不能保證下一輪通過任何 gate。

## 7. 實際讀取檔案與盲檢討聲明

實際讀取：

- `.agents/skills/blind-review-strategy-study/SKILL.md`
- `.agents/skills/blind-review-strategy-study/references/review-method.md`
- `manifests/preregistration.yml`
- `manifests/candidate-definition.yml`
- `manifests/development-trial-inputs.yml`
- `manifests/source-bundle.yml`
- `evidence/development.yml`
- `evidence/development-authorization.yml`
- `src/trading_2026_2/tsm_mean_reversion_reversal_trigger_v001.py`
- `tests/test_tsm_mean_reversion_reversal_trigger_v001.py`
- `pyproject.toml`

本次沒有讀取或使用 `study.yml`、README、正式 historical Evaluation、robustness challenge、replay、terminal evidence/payload、journals、full/quarantine 原始價格快照或外部資料。除本補充筆記外，沒有修改 Study 的 manifest、evidence、events、策略程式或測試。
