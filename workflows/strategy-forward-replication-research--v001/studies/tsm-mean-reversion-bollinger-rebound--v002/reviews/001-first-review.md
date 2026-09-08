# tsm-mean-reversion-bollinger-rebound--v002 盲檢討

## 1. 範圍與結論限制

- Workflow 固定為 `strategy-forward-replication-research--v001`。
- 目標 Study：`tsm-mean-reversion-bollinger-rebound--v002`。
- 本次只使用 preregistration、candidate/qualification 規格、Development evidence、事件生命週期紀錄，以及 Source Bundle 白名單內的程式與測試。
- Development 角色是 2014-01-01 至 2018-12-31，warmup-only 角色是 2013-01-01 至 2013-12-31；沒有開啟任何價格快照。
- 這是盲檢討，不回答、也不推測正式 Historical Evaluation 或 Terminal 的表現與失敗原因。
- 目標路徑缺少白名單所列的 `evidence/provenance.yml` 與 `evidence/selection-evidence.yml`，因此無法獨立查核這兩類證據；本報告仍可根據 Development evidence 檢討設計與已記錄的 Development 結果。

## 2. 實際問題與影響

最重要的問題是「訊號太稀疏，還不足以支持複雜假說」。Development 只有 16 筆完成交易，低於 Workflow gate 的 20 筆，也低於本次事前登記的 30 筆研究目標；五個 signal year 中 2017 年只有 1 筆。這不是正式 Evaluation 失敗的證明，但代表目前沒有足夠觀察量判斷事件記憶與縮量守低是否真的帶來可重複的優勢。

在這 16 筆 Development 交易中，候選的 base return 是 10.8871%、profit factor 是 2.8678、realized maximum drawdown 是 2.5828%；stress return 是 7.5711%、profit factor 是 2.2401、drawdown 是 2.5409%。相較簡化 Bollinger baseline，候選的風險與成本後品質較好，但交易數從 42 筆降到 16 筆。更嚴格的事前研究目標也全部未達：交易數未超過 v009、base/stress 報酬未達 v009，兩種成本模型下的回撤也高於 v009。

事件漏斗也很窄：60 個可建立的放量事件中，34 個失效、10 個到期、16 個確認並實際進場；也就是只有 26.7% 走到成交，56.7% 在守低觀察期內跌破事件 Low。這種篩選可能正是策略想要的風控，但也可能只是把可交易樣本過濾到過少。另有 8/16 筆交易以 time exit 結束，表示固定 10-session 持有期常常等不到停利或停損以外的明確結果，持有期與反轉速度是否相配仍是未驗證假說。

## 3. 規格與實作檢查

### 已核對一致的部分

- Bollinger 使用 Close、20 日窗口、母體標準差 `ddof=0`；事件日成交量除以前 20 個完整 session 的均量，沒有把事件日放入分母。
- 回升確認使用收盤高於前一日，且相對 SMA20 仍低至少 1.5%；候選確認沒有使用 %B 或 RSI。
- 事件觀察只處理事件日後第 1 至第 5 個 session；失效先於縮量守低與回升確認，同日守低與確認可以成立，事件日自身不會完成守低。
- 確認後下一個 session open 才進場；停損／停利的 gap、同日同時觸及時 stop-first、成本內含的整數股風險預算、單一持倉與 5-session cooldown 的主要流程均和 frozen candidate 一致。
- 已核對白名單檔案的 SHA-256：Development evidence、trial inputs、preregistration、candidate/qualification 規格、Source Bundle，以及 Source Bundle 內的 v002 引擎與測試都和各自宣稱的 digest 一致。

### 需要修正或明確化的部分

1. **事件到期當日是否可以建立新事件：規格歧義／實作風險。** Preregistration 只明確禁止「同日失效後」建立新事件；但程式在觀察期到期時也設下 `current_event_ended`，接著同日一律禁止建立新事件。因此，前一事件在第 6 個 session 到期時，如果當日同時出現新的放量條件，會被靜默丟掉。下一輪必須事前寫明這個行為，並加入第 5／第 6 個 session 的邊界測試；若允許到期後重建，應把到期與失效分開處理。

2. **`prior_session_window: 5` 的意義沒有和可執行訊號對齊：規格歧義。** 規格保留了「prior session window 5」及 `prior_volume_spike_ratio`，但候選真正建立事件時使用的是事件當日成交量相對前 20 日均量；程式計算的 prior-volume 欄位不參與正式 candidate event signal，只在合成 smoke adapter 中出現。應在下一輪前選定「事件當日放量」或「此前 5 日放量」其中一個定義，刪除未使用欄位或把它納入明確測試，避免不同執行者得到不同策略。

3. **測試覆蓋不足。** v002 測試涵蓋基本事件、失效優先與 base/stress 生命週期，但沒有覆蓋事件到期邊界、同日守低加確認、active event 遇到新放量不重設、cooldown、fold cutoff、gap stop/target、整數股風險上限等關鍵分支。測試檔另有一項會載入 Historical runner 的測試；本次沒有執行 pytest，以免越過盲檢討的正式結果邊界。

4. **測試用 smoke adapter 不應混在候選引擎的自動決策路徑。** 當資料呈現長段近乎平盤、且沒有 Bollinger bandwidth 時，`backtest` 會改用 `studyctl_smoke_signal`，而不是 frozen candidate signal。Development 的 TSM 資料不符合這組形狀，所以沒有證據顯示它改變本次結果；但同一個 API 依資料形狀切換策略，會讓未來的合成資料或異常資料得到非候選交易。建議移到明示的測試 adapter，或用明確的 test-only 參數隔離。

## 4. Development 穩健度

我從 Development 的 16 筆 raw trade records 重算主要數據，結果和 evidence 一致：

| 指標 | Base | Stress |
|---|---:|---:|
| 完成交易 | 16 | 16 |
| 勝率 | 75.0%（12/16） | 62.5%（10/16） |
| 平均每筆 PnL | 680.44 | 473.20 |
| 平均獲利／平均虧損 | 1,393.00 / -1,457.23 | 1,367.62 / -1,017.51 |
| Return | 10.8871% | 7.5711% |
| Profit factor | 2.8678 | 2.2401 |
| Realized maximum drawdown | 2.5828% | 2.5409% |
| 最大單筆 realized loss fraction | 2.5828% | 2.5409% |

時間分段顯示 2014、2017 為負，2015、2016、2018 為正；2018 只有 3 筆交易卻貢獻 49.34% 的全部正 PnL，前三筆獲利交易合計占 37.98%。這不是目前 gate 的失敗，但表示年度樣本很少，整體正報酬對少數時段仍敏感。

事前指定的 leave-one-signal-year-out 在 stress 下仍為正，最差是移除 2018 年後 return 2.5029%、profit factor 1.4100、drawdown 2.5409%，但剩下只有 13 筆交易。Block bootstrap 的 stress 結果也不是無風險：block length 3 的 5% return 分位數為 -0.1653%，profit factor 5% 分位數為 0.9828%，正報酬比例為 94.632%；block length 5 的對應數字是 1.3053%、1.1399% 與 97.51%。因此診斷支持「大多數重抽樣路徑仍為正」，但不支持把目前的 16 筆當成穩定估計。

機制 ablation 是事前固定且只作診斷，不能拿來改寫本 Study 的選擇。完整候選為 16 筆、base return 10.89%；移除 quiet hold 後為 19 筆、12.90%；移除事件記憶並採 same-day event 為 20 筆、26.26%。stress 也呈現同方向差異。這表示在 Development 中，最複雜的「記住事件再等縮量守低」沒有顯示出相對簡化臂的額外優勢；但這是機制待驗證的警訊，不是正式 Evaluation 的失敗原因。

## 5. 調整優先順序

### A. 規格／實作缺陷：下一輪前先修正

- 明確定義事件在第 6 個觀察 session 到期時，當日新事件可否建立；新增 offset 5、offset 6、失效同日三組測試。
- 對齊 `prior_session_window`、事件當日成交量與 `prior_volume_spike_ratio` 的規格、程式欄位和測試；不要讓名稱暗示一個實際沒有使用的價格／成交量條件。
- 將 smoke adapter 從正式 `backtest` 決策路徑隔離，補上候選訊號不因資料形狀改變的測試。

### B. Development 警訊：新 Study 事前登記後再驗證

- 先解決樣本量問題：本候選只有 16 筆，未達 20 筆 Workflow gate 和 30 筆研究目標；不要在目前 Study 內放寬門檻或繼續搜尋。
- 把「縮量守低是否真的增加資訊」設成單一、事前指定的下一輪比較；可以選擇保留完整機制或移除 quiet hold，但驗收要同時看交易數、成本後結果與時間分段，而不是只挑最高 return。
- 針對 50% time exit 的現象，若要改持有期，應只預先登記一個明確的持有期假說及其副作用（可能增加交易數，也可能增加未完成反轉的損失），不可事後掃描多個持有期。

### C. 未驗證設計假說：保留為新 Study 的問題

- 事件日放量加上後續縮量守低，可能是賣壓減弱的可觀測代理，但目前資料不能證明因果，也不能把成交量解讀成吸籌證據。
- 固定 raw entry 的 ±4% 停損／停利和 10 個持有 session 沿用 v009，確保比較公平；若要改成波動度自適應規則，必須建立新的 preregistration，並預先定義 gap risk、成本 stress 和最低交易數的驗收方式。
- 部位 sizing 只把規定的 stop 價格放入風險預算；遇到 stop gap 時，實際損失仍可能超過預算。本次最大實現損失低於 4% gate，但不足以保證未來 gap 不會放大損失；下一輪應預先登記 gap-loss 診斷或明確的可接受上限。

## 6. 不能得出的結論

本報告不能說明正式 Historical Evaluation 是否通過、失敗，或任何正式失敗的原因；也不能保證上述調整會改善正式結果。正式 Historical Evaluation、Terminal、quarantine 與相關原始價格／payload 均未讀取，也沒有使用網路、券商或外部市場資料。

## 7. 讀取紀錄

Study 內實際讀取：

- `manifests/preregistration.yml`
- `manifests/candidate-definition.yml`
- `manifests/qualification-spec.yml`
- `manifests/development-trial-inputs.yml`
- `manifests/source-bundle.yml`
- `manifests/data-snapshot-acquisition.yml`（只檢查來源、日期、完整性與角色）
- `evidence/development.yml`
- `evidence/development-authorization.yml`
- `events/000001-study-created.yml`、`000002-preregistration-approved.yml`、`000003-development-authorized.yml`、`000004-trial-recorded.yml`、`000005-trial-registry-frozen.yml`（只作生命週期／digest 核對）
- Source Bundle 白名單內的 `pyproject.toml`、`uv.lock`、`src/trading_2026_2/__init__.py`、`src/trading_2026_2/tsm_mean_reversion_bollinger_rebound_v001.py`、`src/trading_2026_2/tsm_mean_reversion_bollinger_rebound_v002.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py`、`tests/test_tsm_mean_reversion_bollinger_rebound_v001.py`、`tests/test_tsm_mean_reversion_bollinger_rebound_v002.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v009.py`；本次只讀取程式與測試，未執行研究 runner。

缺失且未讀取：`evidence/provenance.yml`、`evidence/selection-evidence.yml`。明確未讀取或使用：`study.yml`、README、Historical Evaluation／Terminal evidence、後續事件、journals、terminal/evaluation payload、full/quarantine/historical-evaluation 價格快照。
