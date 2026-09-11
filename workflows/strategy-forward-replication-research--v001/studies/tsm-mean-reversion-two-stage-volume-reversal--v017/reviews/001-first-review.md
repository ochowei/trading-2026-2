# tsm-mean-reversion-two-stage-volume-reversal--v017 盲檢討

## 範圍與結論限制

- Workflow 固定為 `strategy-forward-replication-research--v001`；目標 Study 為 `tsm-mean-reversion-two-stage-volume-reversal--v017`。
- 本次只檢查研究設計、Source Bundle 內允許的程式與測試，以及 2014-01-01 至 2018-12-31 的 Development evidence；2013 年資料只作 warmup 角色。
- scope checker 判定 `blind_review_status: eligible`、`development_evidence_status: available`。本報告沒有讀取或使用正式 Historical Evaluation、Terminal 或其結果，因此不回答正式 Evaluation 為何成功或失敗。

## 實際問題與影響

最重要的問題不是原有 v009 路徑的 Development 數字，而是 v017 新增的「放量事件—縮量回測」路徑在 Development 完全沒有產生新增交易。Evidence 記錄 164 個放量事件，最後分別為 82 個跌破事件低點、53 個被較新事件取代、29 個逾期；補充確認數、補充成交數與被持倉／冷卻阻擋的確認數都是 0。24 筆完成交易全部來自 `original` 路徑，且與 v009 逐筆保留，沒有新增或被排擠的交易。

因此：

- formal Development gates 全部通過，但 candidate freeze 不合格；`disposition: pass` 只代表 formal gates，不能解讀成候選已通過選擇。
- 7 個預先登記 research targets 失敗：交易數 24 未達 30、沒有超過 v009 的 24 筆、淨新增 base/stress PnL 都是 0、沒有新增交易或跨 3 個 signal year 的新增交易，stress return 26.5232% 低於 30.40%。
- 本次 Development 的獲利與穩健度證據實際上只驗證了既有 v009 原有路徑，尚未驗證 v017 新機制是否能帶來可重現的增量。

## 規格與實作檢查

### 已確認一致的部分

程式與 preregistration／candidate definition 的主要邊界一致：事件量至少為過去 20 日平均的 1.25 倍、收盤在日內區間上半部、事件年齡 2 至 5 個交易日、縮量回測不超過事件量 80%、低點只以嚴格跌破事件低點失效、訊號 gap 為 `[1.0%, 1.5%)`，同日原有路徑優先；進場、成本、停損停利、10 個持有 session、冷卻與單一持倉規則也與登記內容相符。

排除 Historical Evaluation runner 後，8 項純合成單元測試全數通過。`pyproject.toml`、v009/v017 程式與 v017 測試的 SHA-256 也與 Source Bundle 登記值一致。這些檢查支持「目前沒有看到把補充路徑誤算進原有路徑」的結論，但不能證明策略假說有效。

### 已確認的診斷層實作問題

`indicators()` 在 `/Users/william/.codex/worktrees/e7b9/trading-2026-2/src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v017.py:220` 固定寫入 `supplemental_retest_seen = False`，而真正的回測狀態只在 `backtest()` 的區域 `active_event` 中更新。若外部使用 `indicators()` 逐日稽核回測，這個欄位會把實際發生的回測誤報成未發生；目前它沒有改變交易結果，但會妨礙事件級別的證據重算。這屬於規格／實作的診斷缺陷，不是正式 Evaluation 失敗原因。

目前 evidence 只有事件終止總數，沒有記錄每個事件是否曾通過縮量回測、在哪一個確認條件被拒絕。因此無法僅靠現有 Development evidence 分辨「機制在資料中幾乎不可達」與「事件可達但 1.0%–1.5% gap、RSI 或收紅條件把它全部濾掉」。

## Development 穩健度

我從 evidence 的 24 筆逐筆交易重算基本統計，與 evidence 相符：

| 口徑 | 完成交易 | 報酬 | Profit Factor | realized 最大回撤 | signal years |
|---|---:|---:|---:|---:|---:|
| base | 24 | 33.6761% | 5.0364 | 1.9998% | 5 |
| stress | 24 | 26.5232% | 4.2042 | 2.1193% | 5 |

交易按 signal year 為 2014/2015/2016/2017/2018 = 6/5/5/2/6。leave-one-year-out 的 stress 最低 Profit Factor 為 3.4092、最低報酬為 18.0304%、最大回撤為 2.1193%；50,000 次交易區塊 bootstrap 在 block length 3/5 的 stress 正報酬比例為 1.0/0.99998，回撤超過 10% 的比例都是 0。這些結果支持既有原有路徑在 Development 期間的內部穩健度，但因 v017 與 v009 完全相同，不能當作補充機制的穩健度證據。

## 調整優先順序

1. **規格／實作缺陷：先修正事件級可觀測性。** 下一個 Study 應讓 `indicators()` 的診斷欄位與實際狀態一致，並逐事件記錄「建立、回測通過、確認條件拒絕、跌破、取代、逾期、被持倉／冷卻阻擋」的唯一終止原因。驗收方式是事件終止原因總數可加總回所有建立事件，且補充訊號能由逐事件紀錄重算。
2. **Development 警訊：不要在本 Study 內調參或 freeze。** 下一輪應先預先登記機制覆蓋率與可達性診斷，確認補充路徑能在至少數個 signal year 產生新增候選，再以既定的增量 PnL、交易數與 stress 門檻判定。這次的 0 筆新增交易不能被當成調低門檻或重跑同一 Study 的理由。
3. **未驗證設計假說：若要改變事件、回測或確認條件，必須建立新 Study。** 任何放寬事件低點失效、延長事件生命週期、改變 volume ratio 或調整確認 gap 的想法，目前都只是下一輪待預先登記的假說；本報告不主張哪一個改法一定能改善正式結果。

## 不能得出的結論

本次不能判斷正式 Historical Evaluation 的表現、失敗原因、是否會在 2020--2024 通過，或上述建議能否改善正式結果。也不能把 Development 的 24 筆原有路徑結果宣稱為 v017 新增機制的驗證。

## 狀態判定

- formal Development gates：`passed`，0 個失敗。
- research targets：`failed`，7 個失敗。
- Development evidence validity：`valid`（evidence 自身標記 `validated: true`）。
- blind review：`eligible`；資格基礎是沒有暴露正式 Evaluation／outcome-bearing Terminal 內容，且未使用 Historical Evaluation 狀態推導資格。
- candidate freeze eligibility：`ineligible`。
- Historical Evaluation status：本次未檢查，且未用於任何結論。
- Study Terminal status：本次未檢查，且未用於任何結論。

## 實際讀取紀錄

本次讀取：

- 盲檢討規範與方法檔：`/Users/william/.codex/worktrees/e7b9/trading-2026-2/.agents/skills/blind-review-strategy-study/SKILL.md`、`/Users/william/.codex/worktrees/e7b9/trading-2026-2/.agents/skills/blind-review-strategy-study/references/review-method.md`。
- Study manifests：`manifests/preregistration.yml`、`manifests/candidate-definition.yml`、`manifests/qualification-spec.yml`、`manifests/development-trial-inputs.yml`、`manifests/source-bundle.yml`、`manifests/data-snapshot-acquisition.yml`。
- Study Development 證據：`evidence/development.yml`、`evidence/development-authorization.yml`。
- 允許的 Source Bundle 程式與測試：`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v017.py`、`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py`、`tests/test_tsm_mean_reversion_two_stage_volume_reversal_v017.py`、`pyproject.toml`；`uv.lock` 僅做 SHA-256 核對，未解讀內容。

沒有讀取或使用 `study.yml`、README、`evidence/historical-evaluation*`、`evidence/terminal-evidence.yml`、`events/000008-*` 及其後事件、`journals/`、Terminal／Evaluation payload、完整／quarantine／Historical Evaluation 原始價格快照，也沒有讀取或執行 Historical Evaluation runner。沒有讀取或使用目標 Study 的正式 Historical Evaluation 或 Terminal 結果。
