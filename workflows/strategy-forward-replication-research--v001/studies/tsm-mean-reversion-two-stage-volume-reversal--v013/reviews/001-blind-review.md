# tsm-mean-reversion-two-stage-volume-reversal--v013 封存式盲檢討

## 先說結論

這一輪的實際問題不是「策略完全沒有交易能力」，而是 v013 新增的提前解禁機制沒有達成它在 Development 階段被要求的比較目標：它只比固定的 v009 多 1 筆交易，卻新增 3 筆提前交易、取代 2 筆原本較好的 v009 交易；新增交易本身在 base 為 -210.07、stress 為 -677.31。結果是交易數略增，但報酬、Profit Factor 與回撤都比 v009 差。這是 Development 警訊，不是正式 Historical Evaluation 的失敗原因。

在目前可讀的規格、策略核心程式與測試中，沒有發現候選訊號或一般交易路徑與 frozen 規格明確不一致。本 Study 應維持 candidate freeze 不具資格，不應在同一 Study 內事後調整規則再重跑。

## 1. 範圍與限制

- 固定 workflow：`strategy-forward-replication-research--v001`。
- 目標 Study：`tsm-mean-reversion-two-stage-volume-reversal--v013`。
- 角色：study 開發者。
- Development signal 期間為 2014-01-01 至 2018-12-31；2013 年只作 warmup。
- scope checker 回報 `blind_review_status: eligible`、`development_evidence_status: available`。本報告只使用研究設計、程式、測試、warmup/Development 角色說明與 Development evidence。
- 沒有讀取、使用或推測正式 Historical Evaluation 或帶有結果的 Terminal 內容；因此本報告不能回答正式 Evaluation 為何成功或失敗。

## 2. Development 的實際問題與影響

Development evidence 的 formal gates 全部通過，但 13 個預先登記的 research targets 中有 10 個失敗，candidate selection 與 candidate freeze 都是不具資格。`disposition: pass` 在這裡只反映 formal Development gates；不能解讀成候選已通過比較目標。

候選與固定 v009 控制組的可重算摘要如下：

| 指標 | v013 base | v009 base | v013 stress | v009 stress |
|---|---:|---:|---:|---:|
| 完成交易數 | 25 | 24 | 25 | 24 |
| 報酬 | 24.399% | 33.676% | 18.167% | 26.523% |
| Profit Factor | 3.353 | 5.036 | 2.742 | 4.204 |
| realized 最大回撤 | 2.362% | 2.000% | 2.596% | 2.119% |

新增交易只有 3 筆，分布在 2015 年 1 筆、2016 年 2 筆，因此新增交易的單一年份占比為 66.67%，新增交易涵蓋年數只有 2 年；這兩項都違反預先登記的分散性目標。三筆新增交易中，一筆 stop、一筆 time、一筆 target-gap；新增 aggregate PnL 為 base -210.07、stress -677.31。相對地，被提前交易排擠的兩筆 v009 交易 aggregate PnL 為 base +7,868.72、stress +6,839.86，所以「新增減被取代」為 base -8,078.79、stress -7,517.17。

候選整體的 stress mark-to-market drawdown 為 3.618%，高於 v009 預先登記的 3.529% 上限；realized drawdown、Profit Factor 與 stress return 也都未達到「不差於 v009」的 targets。這說明提前恢復交易的成本不只是增加交易，而是改變了原本冷卻期所隔開的交易順序。

## 3. 假說、規格與實作檢查

### 已確認一致的部分

1. 正常訊號仍使用 20 日 SMA 負偏離至少 1.5%、簡單 rolling RSI(2) 不高於 50、前 5 個 session 的先行成交量條件與 `Close > prior Close`。
2. 提前機制把退場後第一個完整日的成交量放量當作 setup，事件日不直接進場；只有事件後第 1 至第 3 個 session 同時通過價格、RSI 與收盤方向條件，才在下一個 session open 進場。事件狀態、重疊事件與第五個冷卻日的正常訊號優先順序，均在 v013 狀態機中有對應處理。
3. 進場、10 個完整持有 session、stop/target gap、同日 stop-first、成本內含的風險股數與不可重疊持倉均沿用 v009；測試也覆蓋事件日禁止確認、重疊事件不重設、冷卻到期優先正常訊號、下一開盤進場與持有期。

### 需要修正或明確化的實作風險

#### A. mark-to-market 診斷對 gap exit 的時間順序可能不一致（規格／實作缺陷，診斷層）

`mark_to_market_drawdown` 對所有非 time exit 都先用該日 Low 計算壓力，再換成實際 exit PnL。若是 `target-gap` 或 `stop-gap`，部位其實在當日 open 已按 gap 規則退出，之後的 Low 不應再算作持倉內壓力；目前程式仍會把它算進去。這不影響 formal realized-drawdown gate，但會影響 mark-to-market 診斷，以及使用該診斷的「不高於 v009」研究目標。

下一輪應先固定定義：gap exit 日是否只記錄 open exit 前的可觀察壓力；並加入 target-gap、stop-gap 有「open 後 Low 更差」的單元測試。若團隊刻意採用整日 Low 的最保守估計，則應把這個意圖寫入規格，並確認候選與控制組完全同一口徑。不能把這項診斷問題直接說成正式 Evaluation 的失敗原因。

#### B. XNYS 日曆是上游依賴，不是核心程式 invariant（驗證缺口）

`validate_bars` 會檢查日期遞增、重複、OHLCV 合法性，但不會自行確認每列是 XNYS session。Development 的 acquisition manifest 有列出日曆完整性檢查，因此目前 Development 綁定沒有顯示資料日曆錯誤；不過允許的單元測試使用一般 business-day index，無法驗證交易所假日邊界。下一輪應補一個明確的 XNYS integration test，或把日曆檢查責任與輸入契約寫得更清楚。

#### C. 參數變體有兩個獨立的成交量門檻欄位（未驗證的實作邊界）

v013 同時暴露繼承自 v009 的 `volume_spike_ratio` 與提前事件用的 `early_volume_ratio_minimum`；固定候選兩者都是 1.05，所以本 Study 的固定路徑一致。但 preregistration 另有 volume-ratio parameter variants，下一輪必須明確規定該變體是否同時改動兩個門檻，並以測試驗證。只改其中一個會使「同一參數變體」實際改了不同的機制。

## 4. Development 穩健度

我從 `evidence/development.yml` 的 25 筆交易重算 base/stress 的交易數、總報酬、Profit Factor、realized equity drawdown、最大單筆 realized loss fraction 與年度交易數，均與 evidence 摘要一致。Source Bundle 列出的可讀程式、測試、`pyproject.toml`、`uv.lock` 與 `__init__.py` 雜湊也一致。

- 年度交易數為 2014: 6、2015: 5、2016: 6、2017: 2、2018: 6。2018 貢獻約 41.10% 的 base 總 PnL、43.67% 的 stress 總 PnL，雖未觸發本 Study 的新增波段占比門檻，仍代表獲利有明顯年度集中。
- leave-one-signal-year-out 仍維持正報酬與 Profit Factor > 1；stress 最低 Profit Factor 為 2.094（移除 2014），最低報酬為 10.234%（移除 2018），最大回撤為 2.596%。這支持「Development 結果不只靠單一年份」的有限結論，但 25 筆交易仍不足以把這些診斷當成高把握度證明。
- trade-block bootstrap（3、5 筆交易區塊，各 50,000 次）的 stress 正報酬比例為 99.706% 與 99.498%，超過 10% drawdown 的比例為 0 與 0.002%；這是對既有交易路徑的重抽樣，不是新的市場樣本，也不能抵銷 v013 相對 v009 的比較目標失敗。
- calendar-block bootstrap（63、126 個 session，各 10,000 次）被明確標為 descriptive-only；stress 正報酬比例為 98.89% 與 99.43%。它對日期群聚的描述比單純交易重抽樣更有參考性，但仍只是 Development 內診斷。

設計上最值得注意的是：提前事件與上一筆交易只隔一個完整日開始辨識，可能仍處於同一個下跌波段。成交量 1.05 倍是溫和門檻，配合一次收盤高於前收，不必然代表新的獨立反轉。這是合理但未驗證的經濟假說；本輪三筆新增交易的結果提供警訊，不能把它寫成已證明的正式失敗機制。

## 5. 調整優先順序

1. **最高優先：先修正或定義 gap-exit 的 mark-to-market 計時口徑。** 用專門測試鎖住 open exit 與後續 Low 的關係，再重新計算新的 Study；不要改寫本 Study 的既有 evidence。
2. **最高優先：保留本 Study 的 freeze ineligible 結果。** 不要因為 formal gates 通過就進入下一階段，也不要在本 Study 內放寬門檻或重選候選。
3. **下一個 Study 才驗證機制調整。** 建議只預先登記一個有限方向，例如限制提前重設只發生在明確非 stop 的退場，或提高「事件＋價格確認」的獨立性；實際選哪個方向應在新 Study 的 preregistration 中固定，並保留「新增交易至少分布於 3 年、淨新增減被取代 PnL > 0、報酬/PF/回撤不劣於 v009」這類可否證驗收條件。
4. **補上 integration coverage。** 驗證 XNYS 假日、Development signal_start/signal_end 邊界、baseline 與 v009 的完整結果等價性，以及兩個成交量門檻在 parameter perturbation 中的綁定。此次環境缺少 pandas/pytest，未執行 pytest；因此這些測試覆蓋判斷來自靜態讀取，不宣稱整套測試已通過。

## 6. 狀態判定

| 狀態 | 本次判定 |
|---|---|
| formal Development gates | passed；13 個 gate 均通過 |
| research targets | failed；10 個 targets 失敗 |
| Development evidence validity | valid；evidence 標示已驗證，且本次重算核心統計一致 |
| blind review status | eligible；依 scope checker，未因 historical status 判定資格 |
| Historical Evaluation status | not inspected；本次不讀取、不使用 |
| candidate freeze eligibility | false / ineligible |

## 7. 實際讀取檔案與禁止證據聲明

本次實際讀取：

- `.agents/skills/blind-review-strategy-study/SKILL.md`
- `.agents/skills/blind-review-strategy-study/references/review-method.md`
- 目標 Study 的 `manifests/preregistration.yml`、`candidate-definition.yml`、`qualification-spec.yml`、`development-trial-inputs.yml`、`source-bundle.yml`、`data-snapshot-acquisition.yml`
- 目標 Study 的 `evidence/development.yml`、`development-authorization.yml`、`provenance.yml`
- `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py`
- `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v013.py`
- `src/trading_2026_2/__init__.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v013.py`、`pyproject.toml`、`uv.lock`

`evidence/selection-evidence.yml` 不存在，未以其他檔案替代讀取。沒有讀取 `study.yml`、README、任何 `historical-evaluation-artifacts/`、`evidence/historical-evaluation*`、`evidence/terminal-evidence.yml`、terminal/evaluation payload、後續事件、journals、full/quarantine/historical-evaluation 原始價格快照、其他 Study 或研究 runner。沒有使用網路、broker、外部市場資料或 connector。

本報告是補充性的封存筆記，不是 stage evidence、candidate、source、event、journal、terminal evidence 或 outcome；沒有把它加入事件鏈，也沒有修改既有 Study、程式、測試或 evidence。
