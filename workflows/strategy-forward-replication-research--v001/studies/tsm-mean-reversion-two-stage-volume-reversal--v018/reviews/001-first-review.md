# tsm-mean-reversion-two-stage-volume-reversal--v018 封存式盲檢討

## 1. 範圍與結論限制

- Workflow 固定為 `strategy-forward-replication-research--v001`。
- 目標 Study：`tsm-mean-reversion-two-stage-volume-reversal--v018`。
- Development 角色：2013-01-01 至 2013-12-31 為 warmup-only；2014-01-01 至 2018-12-31 為 Development，使用 TSM、XNYS 日線資料。
- scope checker 回報 `blind_review_status: eligible`、`development_evidence_status: available`；讀取並核對後，Development evidence 為 `valid`。
- 本報告只使用研究設計、程式、測試與 Development evidence。沒有讀取或使用正式 Historical Evaluation、帶 outcome 的 Terminal、quarantine 或 Historical Evaluation 原始資料，因此不回答正式 Evaluation 為什麼可能通過或失敗。

## 2. 實際問題與影響

本 Study 最重要的問題不是 Development 的既有交易表現不好，而是 v018 想驗證的「淺回落補充路徑」在 Development 完全沒有被啟動。Development evidence 記錄 38 個候選 raw signal，但全部是原 v009 路徑；補充路徑為 0 個 raw signal、0 個可進場 signal、0 筆 completed trade、0 個新增 signal year。候選最後 24 筆交易也全部是原 v009 路徑，與 v009 control 的生命週期和指標完全相同。

因此，24 筆交易的收益與穩健度只能說明既有 v009 路徑在這段 Development 資料上的表現，不能當成 v018 新假說已被驗證。formal Development gates 雖然通過，但所有要求「新增交易」或「新增交易年度」的 research targets 均失敗，候選沒有 freeze 資格；不應把這次結果解讀成 v018 已改善 v009。

## 3. 假說、規則與實作對照

### 已對上的部分

- 原有路徑使用 SMA(20) 下方至少 1.5%、RSI(2) 不高於 50、收盤高於前收，以及前 5 個 session 的量先價特徵。
- 補充路徑使用 t-2、t-1 各自相對於「各自前 20 個 session」平均量至少 1.05 倍；t-2 到 t-1 跌幅收斂、t-1 報酬不為正、低點不再降低；訊號日 gap 為 1.0% 至未滿 1.5%、RSI(2) 不高於 50 且收盤高於前收。
- 程式用當日及更早資料計算訊號，下一個 XNYS open 進場；成本、整數股、現金上限、2% stop-risk budget、4% stop、4% target、10 個完整持有 session、adverse-stop-first、5 個 session cooldown 均與登記規格一致。
- v018 的 strategy engine digest 與 `development-trial-inputs.yml` 登記值一致；v018 關閉補充路徑時，程式仍使用 v009 的指標引擎，測試核對原有路徑的交易生命週期、accepted sessions 與 metrics 一致。

### 設計上的主要風險

1. 補充路徑把「兩日放量、跌幅收斂、低點守住」這組 setup，與「淺 gap、RSI、收盤轉強」這組 trigger 全部用 AND 串接。它在概念上清楚，但交集可能過窄；本次 0 個 raw signal 已經是明確的 Development 警訊，不能只看原 v009 的高 PF 來替它背書。
2. 單一部位、10 個持有 session 加 5 個 cooldown 會讓 setup 互相競爭。原路徑已有 9 個 raw signal 被持倉擋下、5 個被 cooldown 擋下；若補充路徑將來啟動，新增 signal 不一定會變成新增 completed trade。
3. formal drawdown 只看已完成交易的 realized equity curve。Development 的持倉內 Low mark-to-market drawdown 為 base 3.30%、stress 3.53%，高於 realized drawdown 的 2.00% 與 2.12%。這不是規格不一致，但說明正式 gate 沒有完全反映持倉中的日內壓力；stop gap 也可能使實際單筆損失超過事前 stop-risk budget。

## 4. 規格與實作檢查

### 未發現的固定候選規格缺陷

在本次允許的檔案範圍內，沒有找到固定 v018 candidate 的直接規格／實作不一致。原路徑 lifecycle match、成本與 gap fill、同日 stop 優先、進出場時點、cooldown anchor 都有程式或測試支持。

### 應在下一輪修正的實作韌性問題

- `v018.py` 的補充條件讀取 `sma_20`、`rsi_2` 這些固定欄位名稱，但 `StrategySpec` 同時暴露可變的 lookback 參數。固定候選的預設值沒有造成這次 mismatch；若下一輪改 lookback，可能變成仍計算固定 20／2，或直接取不到欄位。應在新 Study 前把欄位命名參數化，或明確拒絕非預設 lookback，並用非預設設定測試驗收。
- v018 測試檔包含會載入 `run_historical_evaluation.py` 的測試。本次沒有執行整個測試套件，以免越過盲檢討讀取邊界；下一輪應把 outcome-dependent tests 與 blind-safe unit tests 分開，避免一般測試命令意外接觸封存結果。

## 5. Development 穩健度

以下數字由 `evidence/development.yml` 的 24 筆逐筆交易與其診斷重算／核對，全部是 Development 內結果：

| 指標 | base | stress |
|---|---:|---:|
| completed trades | 24 | 24 |
| return | 33.68% | 26.52% |
| profit factor | 5.04 | 4.20 |
| realized maximum drawdown | 2.00% | 2.12% |
| maximum realized trade loss fraction | 2.00% | 2.00% |
| traded years | 5 | 5 |

交易按 signal year 為 2014: 6、2015: 5、2016: 5、2017: 2、2018: 6。base 有 20/24 筆獲利，stress 有 18/24 筆獲利；exit reason 為 target-gap 7、target 8、time 6、stop 3。最大單一年度 base PnL 來自 2018，約占總 Development PnL 32%，沒有看到單一年份超過一半的集中現象，但 2017 只有 2 筆交易，樣本仍小。

事前指定的 leave-one-signal-year-out 在 stress 下，最低 profit factor 為 3.41、最低 return 為 18.03%，最大 drawdown 為 2.12%。block bootstrap（block length 3／5、各 50,000 次）stress 正報酬比例為 100%／99.998%，第 5 百分位 return 約 15.83%／15.88%，第 5 百分位 profit factor 約 2.32／2.33。這些數字支持「既有原路徑的 Development 交易序列沒有明顯單一年份崩潰」；但 bootstrap 仍建立在只有 24 筆、且全部來自 v009 原路徑的交易上，不能補足 v018 補充機制沒有觀測值的問題。

## 6. 調整優先順序

1. **Development 警訊：先修正「機制未啟動」的研究判讀。** 新 Study 應在 formal performance gate 之前預先登記 activation gate，例如至少有 1 筆補充 raw signal、且至少出現在 3 個 signal years；同時保留 raw signal、可進場、被持倉／cooldown 阻擋與 completed trade 的分層統計。驗收是能區分「條件太稀疏」與「有訊號但被執行規則吞掉」；副作用是可能排除低頻但有經濟意義的 setup，所以仍需由新假說事前說明。
2. **規格／實作缺陷：修正 lookback 欄位契約與測試隔離。** 問題是可變設定與固定欄位名稱不一致，或測試命令可能載入 outcome runner。驗收是非預設 lookback 會正確改變欄位或明確報錯，blind-safe test 命令不會觸碰 historical runner；副作用是介面會更嚴格，但可避免下一輪把設定變更誤當成已生效。
3. **未驗證設計假說：不要在本 Study 內調參。** 下一輪若仍主張淺回落均值回歸，應另建新 Study，事前固定補充條件的組合、單部位／cooldown 互動與 v009 comparison control，並把 net incremental PnL 和新增交易年度當成獨立驗收。不能根據本次 0 signal 事後挑一個較寬的 gap 或較低的成交量門檻來重跑本 Study。
4. **未驗證設計假說：把開倉中的壓力列為明確研究目標。** 若仍採 4% stop／4% target／10-session holding，下一輪可事前固定 mark-to-market drawdown 與 gap-loss 的限制，並說明它與 realized gate 的不同。可能副作用是 gate 更嚴格；驗收是兩種 drawdown 都能從同一份 Development evidence 重算，而不是只用成交後 PnL。

## 7. 不能得出的結論

- 不能說 v018 已改善正式 Evaluation 的表現；本次 Development 沒有任何 v018-only trade。
- 不能把 Development 的高 return、PF 或 bootstrap 結果當成正式 Historical Evaluation 的結果。
- 不能判斷正式 Evaluation 的失敗原因、是否會通過，或任何後段交易與年度表現；這些資料在本次盲檢討中沒有讀取，也沒有用於建議。

## 8. 狀態判定

| 狀態 | 本次判定 |
|---|---|
| formal Development gates | passed |
| research targets | failed：24<30、沒有超過 v009 的交易數、沒有新增交易／年度、net new minus displaced PnL 為 0 |
| Development evidence validity | valid，已驗證 |
| blind review status | eligible；依 scope checker 的 outcome 未曝光判定，不依 Historical Evaluation 狀態推導 |
| Historical Evaluation status | `not_inspected`；本次不讀取、不使用 |
| candidate freeze eligibility | ineligible / false |

## 9. 實際讀取的檔案與盲性聲明

本次實際讀取：

- `.agents/skills/blind-review-strategy-study/SKILL.md`
- `.agents/skills/blind-review-strategy-study/references/review-method.md`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/manifests/preregistration.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/manifests/candidate-definition.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/manifests/qualification-spec.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/manifests/development-trial-inputs.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/manifests/source-bundle.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/manifests/data-snapshot-acquisition.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/evidence/development.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/evidence/development-authorization.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v018/evidence/provenance.yml`
- `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v018.py`
- `tests/test_tsm_mean_reversion_two_stage_volume_reversal_v018.py`
- `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py`
- `tests/test_tsm_mean_reversion_two_stage_volume_reversal_v009.py`
- `pyproject.toml`
- `uv.lock`

明確聲明：本報告沒有讀取或使用目標 Study 的正式 Historical Evaluation 結果、outcome-bearing Terminal、`evidence/historical-evaluation*`、`evidence/terminal-evidence.yml`、`events/000008-*`、`journals/` 或 full／quarantine／historical-evaluation 原始價格快照。本檔案是補充性的 review note，不是 stage evidence、candidate、event、terminal evidence 或 outcome。
