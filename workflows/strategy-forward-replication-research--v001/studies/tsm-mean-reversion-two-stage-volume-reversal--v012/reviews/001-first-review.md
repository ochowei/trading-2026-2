# tsm-mean-reversion-two-stage-volume-reversal--v012 封存式盲檢討（001）

- 檢討角色：study 開發者
- workflow：`strategy-forward-replication-research--v001`
- Study：`tsm-mean-reversion-two-stage-volume-reversal--v012`
- 檢討日期：2026-09-07
- Development 期間：2014-01-01 至 2018-12-31
- warmup 期間：2013-01-01 至 2013-12-31

本檔是補充性的封存筆記，不是 stage evidence、candidate、event、terminal evidence 或 outcome；不會改寫既有 digest，也不會改動 Study 的規格、程式或資料。

## 1. 範圍與結論限制

這是 blind review。我只使用研究設計、repository 內的策略程式與測試，以及既有 Development evidence。原始價格快照沒有被開啟；資料 manifest 只用來確認來源、日期、完整性與角色。沒有讀取或使用目標 Study 的正式 Historical Evaluation 或 Terminal 結果，因此本檢討不回答正式 Evaluation 是否通過，也不推測正式結果的失敗原因。

## 2. 實際問題與影響

最重要的問題不是目前看得到明顯的價格偷看未來，而是新增的「同日盤中反轉」條件比較像候選情境，不足以當成隔日開盤可交易的反轉觸發器。它允許當日收盤高於開盤、收在日內高低區間上方三分之一，但沒有要求下一個 session 仍然確認買方承接；隔日跳空下跌時，這個條件可能把弱反彈直接轉成停損交易。

Development evidence 對這個風險提供了直接警訊：候選共有 28 筆交易，其中 22 筆是原 v009 確認、6 筆是真正新增的盤中反轉交易。6 筆新增交易中 5 筆虧損、1 筆獲利；新增交易合計 PnL 為：

- base：`-10,437.5800`
- stress：`-10,283.9589`

因此新增交易本身沒有達到預先登記的兩個模型都必須嚴格大於零的選擇目標。這說明新增分支目前沒有補足原 v009 的訊號品質，反而替換掉部分原有交易機會。

## 3. 設計與規則對照

### 3.1 假說的實際含義

規格要求保留 SMA(20) 至少 1.5% 的超跌、RSI(2) 不高於 50、前五個 session 的成交量先行條件，再以「收盤高於前收」或「收盤高於開盤且收在日內上三分之一」作為確認。這個 OR 把兩種經濟含義不同的訊號放在同一個候選中：

1. 原 v009 的收盤相對前收轉強；
2. 收盤仍不高於前收，但盤中看起來有承接的反彈。

若兩者共用同一個候選門檻，總體報酬可能掩蓋第二種訊號的獨立風險。這次 evidence 已經分開標示確認類型，而新增分支的交易結果顯示它是主要需要重新驗證的部分。

### 3.2 Development 穩健度

候選的 Development 指標如下：

| 指標 | base | stress |
|---|---:|---:|
| 完成交易 | 28 | 28 |
| return | 21.7961% | 15.3804% |
| profit factor | 2.1661 | 1.8488 |
| realized maximum drawdown | 5.8799% | 5.8784% |
| 最大單筆實現虧損 | 2.5590% | 2.5189% |

預先登記的 Development gates 中，`completed_trades` 要求至少 30 筆、stress profit factor 要至少 3.2056、stress return 要嚴格高於 26.5904%。既有 Development evidence 將這三項列為未通過；其餘列出的 Development gate 通過。這是 Development 階段的資格結果，不是正式 Evaluation 結果。

和控制組比較，候選也沒有顯示新增複雜條件帶來改善：

| 組別 | 交易數 | base return / PF | stress return / PF |
|---|---:|---:|---:|
| v009 | 24 | 33.6761% / 5.0364 | 26.5232% / 4.2042 |
| v010 | 29 | 34.7898% / 3.8375 | 26.5904% / 3.2056 |
| 簡單 baseline | 28 | 22.4598% / 2.2433 | 15.9644% / 1.9088 |
| v012 候選 | 28 | 21.7961% / 2.1661 | 15.3804% / 1.8488 |

候選在每個 signal year 都有交易。2018 年 8 筆交易的 stress PnL 為負，但 leave-one-signal-year-out 的五個 stress 結果仍全部為正，最低 return 為 7.9373%、最低 profit factor 為 1.4717。這表示現有交易池的正報酬不是只靠單一年份；但它不能抵銷新增盤中反轉交易合計虧損的訊號品質問題。

trade-block bootstrap 的 stress positive-return ratio 在 3-session 與 5-session 區塊分別為 93.758% 與 95.916%，且通過既定 trade-block gate。不過保留日曆群聚的 descriptive-only bootstrap 顯示，63-session 區塊的 stress drawdown 超過 10% 比例為 13.71%，第五百分位 return 為 -2.4422%；126-session 區塊仍為 8.80% 與 -1.1470%。這代表結果對日期群聚的尾端風險仍有明顯不確定性，不能只看交易重抽樣的正報酬比例。

## 4. 規格與實作檢查

### 4.1 已核對且未發現不一致的部分

`v012` 的 `indicators` 先關閉 v009 的收盤高於前收限制，再依規格以 OR 合併原確認與盤中反轉確認；盤中區間為 `High - Low`，使用 `Close > Open`、`Close <= prior_close`、`High > Low` 及收盤位置大於等於 `2/3`。這和 preregistration 及 candidate definition 一致。

沿用並複製的交易生命週期也和規格相符：訊號收盤後下一個 session open 進場、最多一個部位、不借款、成本納入 stop 風險預算、10 個完整持有 session 後下一個 open time exit、gap 依 open 成交、同日同時觸及時 stop 優先，並以 completed-position-exit 起算 5 個 session 的 cooldown。沒有在目前檢查中確認到訊號日使用未登記的隔日資料、進場日錯位或 stop/target 優先順序錯誤。

Source Bundle 列出的 repository source 與測試檔案雜湊均與 manifest 一致。

### 4.2 驗證缺口與證據限制

目前 v012 的測試檔主要覆蓋盤中反轉條件、收盤位置邊界與平盤區間；沒有直接覆蓋 v012 自己的 next-open 進場、cooldown、10-session time exit、gap fill、同日 stop-first、成本內含 sizing 或 `signal_end` 完整生命週期。這不是已確認的規格錯誤，但因 v012 複製了 v009 的 backtest，若未來只改其中一份，測試不一定能及時發現漂移。下一輪應把這些交易生命週期條件加入 v012 的專屬測試。

另外，preregistration 固定了 `price_only` 與 `volume_only` 兩個 mechanism-ablation arms，但 Development evidence 沒有提供這兩個 arms 的結果；目前只能比較簡單 baseline、v009、v010 與 v012，不能完整判斷成交量條件或方向條件各自的邊際作用。`evidence/provenance.yml` 與 `evidence/selection-evidence.yml` 也未找到，因此本次沒有進行獨立的 provenance 或 selection-evidence 審核，只使用 Development evidence 內的 bindings 與交易比較欄位。

## 5. 調整優先順序

### 第一優先：Development 警訊

不要把目前的 OR 候選原樣帶入下一輪。下一輪應把「原 v009 確認」與「同日盤中反轉」拆成可分辨的預先登記 arms，並要求新增 arm 在 base 與 stress 的 exact-lifecycle-key 配對後合計 PnL 都大於零；同時保留交易數、stress PF、stress return 與風險門檻。預期可解決的問題是新增訊號以五筆停損換取一筆獲利；副作用是交易數可能下降，這應由下一輪事前門檻接受或否決。

### 第二優先：未驗證設計假說

把「隔日仍需確認」或「延後一個 session 才進場」當成全新的 Study 假說，而不是回寫本 Study。可否證的驗收方式是事前固定進場時點、成本、持有期與比較控制，並要求新 arm 的新增交易在兩種成本模型都不再為負，且不靠單一年度或短日曆區塊支撐。這可能降低容量並錯過快速反彈，需和較少的假訊號交換評估。

### 第三優先：規格／實作驗證缺口

目前沒有足夠證據要求修改 frozen strategy code；應先補齊 v012 的交易生命週期測試與四個預先登記消融 arms 的 Development 證據，再開始下一輪。驗收標準是測試可明確驗證 next-open、cooldown、持有期、gap、stop-first、成本與 fold 邊界，且每個預先登記的 diagnostic arm 都有可重算的輸出。

## 6. 不能由本次檢討得出的結論

- 不能判斷正式 Historical Evaluation 的 pass/fail。
- 不能把 Development 的 gate failure 說成正式 Evaluation 的失敗原因。
- 不能保證延後進場、拆分 arms 或補測試後一定改善未來結果。
- 不能用本次盲檢討推測任何未讀取的 quarantine、Historical Evaluation 或 Terminal 結果。

## 7. 讀取紀錄

本次實際讀取：

- `.agents/skills/blind-review-strategy-study/SKILL.md`
- `.agents/skills/blind-review-strategy-study/references/review-method.md`
- `workflows/strategy-forward-replication-research--v001/workflow.yml`
- `workflows/strategy-forward-replication-research--v001/rules/state-machine.yml`
- `workflows/strategy-forward-replication-research--v001/rules/evidence-requirements.yml`
- `workflows/strategy-forward-replication-research--v001/rules/workflow-floors.yml`
- 目標 Study 的 `manifests/preregistration.yml`、`candidate-definition.yml`、`qualification-spec.yml`、`development-trial-inputs.yml`、`source-bundle.yml`、`data-snapshot-acquisition.yml`
- 目標 Study 的 `evidence/development.yml`、`evidence/development-authorization.yml`
- `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py`
- `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v010.py`
- `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v012.py`
- `tests/test_tsm_mean_reversion_two_stage_volume_reversal_v012.py`
- `pyproject.toml`

另以雜湊核對 Source Bundle 列出的 `src/trading_2026_2/__init__.py` 與 `uv.lock`，未作內容分析。

本次沒有讀取 `study.yml`、README、任何 `evidence/historical-evaluation*`、`terminal-evidence.yml`、後段事件、journals、quarantine 或 Historical Evaluation 原始價格快照，也沒有使用網路、外部市場資料、券商資料或 connector。明確聲明：本次沒有讀取或使用目標 Study 的正式 Historical Evaluation 或 Terminal 結果。
