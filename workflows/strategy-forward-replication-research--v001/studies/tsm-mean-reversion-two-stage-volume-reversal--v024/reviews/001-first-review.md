# v024 Study 封存式盲檢討（001）

## 1. 範圍與結論限制

- Workflow：`strategy-forward-replication-research--v001`。
- Study：`tsm-mean-reversion-two-stage-volume-reversal--v024`。
- 角色：study 開發者。
- `check_scope.py` 回報 `blind_review_status: eligible`、`blind_review_eligible: true`，且未因 Historical Evaluation 或 Study terminal 狀態推導資格。
- Development 角色為 2013 年 warmup、2014-01-01 至 2018-12-31 signal view；資料規格為 XNYS、日線、Yahoo auto-adjust OHLCV。
- 本次只使用 preregistration、candidate definition、qualification spec、Development inputs/evidence、provenance、固定程式與測試。這份檔案是補充性的 review note，不是 stage evidence、candidate、source、event、journal、terminal evidence 或 outcome。
- 本報告不回答、也不推測正式 Historical Evaluation 的表現或失敗原因。正式 Evaluation、terminal payload、journal、full／quarantine／historical-evaluation 資料均未讀取。

## 2. 實際問題與影響

最重要的問題不是 v024 沒有產生交易，而是補充路徑增加交易後，沒有在壓力成本下維持 v009 的風險與相對報酬。Development evidence 的 35 筆 candidate 交易雖通過所有 formal Development gates，但事前登記的比較性 research targets 有四項失敗，因此不能凍結候選。

與 v009 control 的同口徑比較如下：

| 指標 | v024 candidate | v009 control | 影響 |
|---|---:|---:|---|
| 完成交易數 | 35 | 24 | 增加 11 筆 |
| base return | 33.874% | 33.676% | 僅增加 0.20 個百分點 |
| base realized maximum drawdown | 5.880% | 2.000% | 增加 3.88 個百分點 |
| stress return | 24.715% | 26.523% | 減少 1.81 個百分點 |
| stress realized maximum drawdown | 5.880% | 2.119% | 增加 3.76 個百分點 |
| stress mark-to-market drawdown | 6.449% | 3.529% | 增加約 2.92 個百分點 |

按完成交易的 `entry_mode` 重算，11 筆 supplemental-origin 交易在 base 合計約 `$2,290.78`、Profit Factor 約 1.27；在 stress 合計只剩約 `$342.42`、Profit Factor 約 1.04，且 11 筆中有 5 筆虧損。這表示補充路徑對成本與滑價相當敏感；這是 Development 警訊，不是正式 Evaluation 的失敗歸因。

單事件狀態機也造成明顯的組合路徑互動：59 個放量事件中，41 個開始追蹤、17 個確認、16 個失效、8 個到期、18 個在已有事件追蹤時被忽略；17 個確認中有 3 個被 cooldown 阻擋、3 個被持倉阻擋，最後只有 11 個 supplemental confirmation 被接受。保守的 lifecycle 配對顯示 stress 的 `net_new_minus_displaced` 為 `-$1,598.34`；把保留交易的時點／資金曲線差也納入後，`net_added_minus_temporally_displaced` 為 `-$1,808.53`。

## 3. 規格與實作檢查

### 已確認一致的部分

- v009 原路徑沿用 20 日 SMA 負偏離、RSI(2)、前置 5 session 成交量與收盤高於前一日；補充路徑使用排除事件日的前 20 session 平均量、前 5 session 高點、上升趨勢條件與事件後第 1--5 個 session 的嚴格突破確認。
- 事件日不確認、不進場；固定突破價為 `max(previous_five_high, event_high)`；事件失效、第五日到期、單一事件追蹤、確認即消耗與原路徑優先等規則均在程式中有對應狀態處理。
- 交易執行符合登記內容：下一個 XNYS open 進場、gap 以 open 成交、同日停損優先、10 個完整持有 session 後於下一個 open time exit、完成出場後 5 session cooldown、2% 風險預算、現金上限、不借款，以及 base／stress 成本模型。
- 靜態核對未發現已確認的訊號偷看未來、事件日資料倒灌、持倉重疊或原路徑生命週期不一致。v024 原始程式與測試的 SHA-256 也分別符合 source bundle 登記的 `b9560c...` 與 `f3a9ca...`。
- 測試涵蓋事件日禁止確認、第五日到期順序、等於突破價、失效、追蹤中忽略新事件、signal cutoff、下一日進場，以及補充路徑關閉後與 v009 的生命週期相等；本次只讀取測試，沒有執行回測或測試。

### 設計風險（不是已確認程式錯誤）

1. 同一套 ±4% stop／target、10 session 持有期與 2% 風險預算同時套用在均值回歸與突破型 supplemental 交易。突破路徑的波動環境可能不同，卻沒有以事件波動或突破距離調整部位與出場；較高的 mark-to-market drawdown 與 supplemental stress Profit Factor 1.04 支持把它列為下一輪優先驗證的假說。
2. 趨勢、放量、固定突破價、五日確認、失效與單事件狀態機被事前固定成一個不可拆分機制；ablation 只作描述性診斷、不參與選擇，且 `price_only` 沒有交易。因此目前不能知道壓力惡化主要來自哪一個條件，也不能把改善歸因於單一條件。
3. 單一 sleeve、原路徑優先與 cooldown 會讓新訊號改變既有交易的時點與資金路徑。這些是登記的行為，不是程式錯誤，但代表「增加交易數」不等於「增加獨立的正貢獻」。

### 證據治理缺口

- Study 內的 `manifests/data-snapshot-acquisition.yml` 不存在；`development-trial-inputs.yml` 與 Development evidence 仍提供資料 digest、日期與角色，但本次沒有沿路讀取 research 副本補洞。
- Study 內的 `evidence/selection-evidence.yml` 不存在；候選凍結資格仍可由 Development evidence 的明確欄位判定為 `false`，但完整 selection evidence 稽核不完整。
- `evidence/development-authorization.yml` 將 `trial_registry_frozen` 記為 `false`，而 `evidence/provenance.yml` 記為 `true`。這是證據 metadata 不一致，應在下一輪修補；它不應被解讀為策略本身或正式 Evaluation 的結果。

## 4. Development 穩健度

我從 `evidence/development.yml` 的 35 筆交易明細獨立重算，結果與 evidence 摘要一致：

- base：26 勝、9 負，Profit Factor `2.8059`，return `33.8742%`，realized maximum drawdown `5.8799%`，最大單筆實現虧損約 `1.9998%`，最長連敗 3 筆。
- stress：24 勝、11 負，Profit Factor `2.3480`，return `24.7146%`，realized maximum drawdown `5.8797%`，最大單筆實現虧損約 `2.0000%`，最長連敗 3 筆。
- signal year 交易數為 2014／2015／2016／2017／2018 的 `11／5／8／3／8`。2018 約貢獻 base 的 35%、stress 的 37%；leave-one-year-out 仍全部維持正 return，表示 Development 的正報酬不是只靠單一年份，但 2017 的交易數只有 3 筆，分段不確定性仍高。
- 事前指定的 50,000 次 block bootstrap 在 stress 下，block length 3／5 的正報酬比例為 `98.454%`／`99.290%`，回撤超過 10% 的比例為 `4.908%`／`2.190%`；block length 3 的最大回撤 95% 分位數約 `9.994%`，已接近 10% formal gate。這支持「單獨看 candidate 仍多數為正」，但也顯示尾端回撤離門檻不遠。
- stress leave-one-year-out 的 return 約為 `15.64%` 至 `23.81%`、Profit Factor 約為 `2.11` 至 `2.61`、maximum drawdown 約為 `3.84%` 至 `5.88%`；這是穩健度的正面訊號，但不能抵銷相對 v009 的四項 research target 失敗。

## 5. 調整優先順序

### 第一優先：規格／證據治理修補

補齊 data-snapshot acquisition 與 selection evidence，並統一 `trial_registry_frozen` 的真實狀態與 digest 綁定。驗收方式是 scope／manifest 驗證可重現、資料角色與日期可獨立核對，且 candidate freeze 的失敗理由與 evidence metadata 一致。這不是調參，也不能用來改寫本 Study 的結果。

### 第二優先：Development 警訊——先驗證風險與成本敏感度

下一個 Study 應只預先登記一個有限的執行／風控假說，例如只改 supplemental-origin 的波動調整部位或出場幾何，保留 v009 原路徑、事件規則與比較控制不變；不要在同一 Study 內擴張參數網格。驗收至少應包含 supplemental 增量 stress PnL 為正、candidate stress return 不低於 v009，以及 stress drawdown 不高於 v009；可另把 mark-to-market drawdown 設為研究目標。

### 第三優先：未驗證設計假說——拆開機制與組合互動

若下一輪要回答「哪一部分機制有效」，應事前固定一個單一比較候選，清楚定義是測試事件條件、確認條件，還是優先／cooldown 互動；不能用本 Study 的描述性 ablation 事後挑選最好的條件。`supplemental_only` 的 12 筆交易低於本 Study 的 20 筆 formal trade gate，只能當診斷背景，不能直接視為已具候選資格。

## 6. 不能得出的結論

本報告不能判斷 v024 在正式 Historical Evaluation 是否通過、是否失敗，也不能把 Development 的相對回撤／stress 增量結果說成正式 Evaluation 的失敗原因。正式結果仍應保持封存，並由獨立的 Historical Evaluation 流程一次性驗證。

## 7. 狀態判定

| 狀態 | 本次判定 |
|---|---|
| formal Development gates | `passed`；evidence 列出的 13 項全部通過 |
| research targets | `failed`；4 項失敗：base 回撤不高於 v009、stress return 不低於 v009、stress 回撤不高於 v009、net incremental stress PnL 為正 |
| Development evidence | 可取得；evidence 自述 `valid`／`validated: true`，本次已獨立重算交易摘要，但 scope checker 本身回報 `not-validated`，且存在上述 metadata 缺口 |
| blind review | `eligible`；依 scope checker，沒有明確曝光的正式 outcome 或帶結果 Terminal 內容 |
| Historical Evaluation | `not_inspected`；本次刻意不讀取，不能據此推導狀態 |
| candidate freeze eligibility | `false`／`ineligible`；由四項 research target 失敗造成 |

## 8. 本次實際讀取的檔案

- `.agents/skills/blind-review-strategy-study/SKILL.md`
- `.agents/skills/blind-review-strategy-study/references/review-method.md`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v024/manifests/preregistration.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v024/manifests/candidate-definition.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v024/manifests/qualification-spec.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v024/manifests/development-trial-inputs.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v024/manifests/source-bundle.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v024/evidence/development.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v024/evidence/development-authorization.yml`
- `workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v024/evidence/provenance.yml`
- `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v024.py`
- `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py`
- `tests/test_tsm_mean_reversion_two_stage_volume_reversal_v024.py`
- `tests/test_tsm_mean_reversion_two_stage_volume_reversal_v009.py`

下列允許路徑在 Study 內不存在，因此沒有內容可讀：`manifests/data-snapshot-acquisition.yml`、`evidence/selection-evidence.yml`。

明確聲明：本次沒有讀取或使用目標 Study 的正式 Historical Evaluation 結果、outcome-bearing Terminal 內容、`study.yml`、`events/000008-*` 以後事件、`journals/`、evaluation／terminal payload、full／quarantine／historical-evaluation 原始價格快照或外部資料。
