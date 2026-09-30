# TASK-036 設計 checkpoint（prepare 前）

**狀態：等待專案管理者審核。** 本文件只是設計草案，尚未呼叫 `prepare`、`create`、Development 或 runner，也尚未在 v005 `studies/` 下建立 Study。

## 派工、角色與唯一性

- Study ID：`tsm-divergence-sma20-sma50-regime--v001`。
- 派工：`.study-developer/assignments/TASK-036-v005.yml`，`source_id=codex-project-manager-task:TASK-036`、`workflow_version=v005`、`scope=development-to-freeze`、角色為 `study 開發者`；目前受派者是 `/root/task_036_trend_regime`。
- 派工檔已由 PM canonicalize，並通過 v005 `load_canonical`；canonical SHA-256：`308a2b80aa35521c16cd4b50173f5c274d276c0e0fbddf512aa81ec2f3ce3f8b`。
- 執行 authority root：repository-local `.authority/`；執行時明示 `--role 'study 開發者'`。
- Identity：`research_round_id=tsm-divergence-sma20-sma50-regime--v001`、`experiment_family=tsm-mean-reversion-v009-sma20-sma50-regime`、`research_owner=ochowei@gmail.com`、`historical_evaluation_operator=operator A`。
- 已搜尋所有 Workflow Package 的 `studies/` 目錄，沒有此 Study ID；再搜尋各 Study preregistration 與研究設計檔（candidate definition、implementation contract）中 SMA(20) 與 SMA(50) 的組合，未找到相同研究。只有通過 PM 審核後才會建立此 Study。

## 固定 Control 與唯一候選差異

- **Control**：原始 `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_v009.py` 的完整 v009 two-stage reversal，使用 `DEFAULT_SPEC`。保留 SMA(20) 超跌至少 1.5%、RSI(2) <= 50、前五個已完成 session 內的 prior-volume ratio >= 1.05、訊號日 Close > 前一 session Close。沿用 v009 的單一持倉、5 個完整 session 冷卻、次一 XNYS session open 入場、4% 停利、4% 停損、10-session time exit、2% 進場前權益風險預算與成本。不可使用 v009 模組內關閉量先與收盤反轉確認的 `BASELINE_SPEC` 代替 Control。
- **Candidate**：完整保留同一條 v009 訊號及所有交易執行設定；只有訊號日收盤時新增 `SMA20 > SMA50` 條件。唯一候選 ID：`tsm-mr-v009-sma20-over-sma50-regime-v001`；唯一 Control ID：`tsm-mr-v009-two-stage-volume-reversal-control-task036-v001`。
- **SMA 定義**：資料用同一份 auto-adjusted Close；每個 XNYS completed session `t`，`SMA20_t` 是 Close[t-19:t] 的 20 筆簡單算術平均，`SMA50_t` 是 Close[t-49:t] 的 50 筆簡單算術平均。兩個區間都包含訊號日收盤，不讀取 t 之後資料；只有嚴格 `SMA20_t > SMA50_t` 才保留訊號，相等或 SMA(50) 尚未就緒時 Candidate 不接受訊號。訊號在收盤後確認，最早仍於下一個 XNYS session open 成交。不得加入 SMA(50) 斜率、動能或其他 filter。
- 假說方向為 Candidate 減 Control；唯一預登記候選、最多 1 trial、固定單候選資格判斷、不做 outcome ranking、不擴充候選家族。不得依 TASK-035 的結果調整任何規則。

## 資料與 Active v005 綁定

- 唯一資料檔：`research/market-data/yahoo/TSM-warmup-development--sha256-a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7.csv`。
- SHA-256：`a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7`；header 為 `Date,Open,High,Low,Close,Volume`，共 1,510 筆資料列，涵蓋 2013-01-02 至 2018-12-31（warmup 2013、Development 2014–2018）。本 checkpoint 只核對此 warmup+Development 檔的 digest、header 與日期端點，不讀其他資料期間。
- 資料綁定預計使用單資產 `data_path`／`data_digest`；`data_bindings` 指向同一檔案及 TSM、Yahoo、`America/New_York`、`after-close`、`warmup-development`。SMA 指標僅用訊號日及更早的已完成資料。
- Active Workflow Package：`workflows/strategy-forward-replication-research--v005`，version `v005`。以 package 的正式 resolver 建立及驗證 reference，並核對 release record、manifest、Workflow 與 Policy；結果一致：
  - `workflow_digest=2441c16d2c477afef9d4d9ca159e3a8bff150080b8552991d5da5fbcc9daf2c2`
  - `release_manifest_path=workflows/strategy-forward-replication-research--v005/release-manifest.yml`
  - `release_manifest_digest=6cf440bf81e2c081ff6e77025c5779cf5f2e4849015278419b836c0777db6405`
  - `policy_set_digest=c86066b33119366a3172f475ff75f8813ba4b7545571894edfe581afabe32215`
  - `resolver_version=1`、`reference_mode=repository-workflow-package`
  - 預計 Study reference path 為 `manifests/workflow-reference.yml`；reference canonical SHA-256 為 `40396c0c742a653a589c5bfb738358149ae7c4302e55dc732362975902af3b90`。正式 release record 綁定的 workflow digest 及 manifest digest 均與 resolver 輸出相同。

## Gates、targets 與固定執行規格

- **13 項 Development formal eligibility gates**，沿用 v005 支援的 v009 Study 門檻：`base_profit_factor > 1.10`、`base_return > 0`、`completed_trades >= 20`、`maximum_realized_trade_loss_fraction <= 0.04`、`maximum_stress_block_bootstrap_drawdown_above_10pct_ratio <= 0.10`、`maximum_stress_leave_one_year_out_drawdown <= 0.10`、`minimum_stress_block_bootstrap_positive_return_ratio >= 0.80`、`minimum_stress_leave_one_year_out_profit_factor > 1.00`、`minimum_stress_leave_one_year_out_return > 0`、`stress_maximum_drawdown <= 0.10`、`stress_profit_factor > 1.00`、`stress_return > 0`、`traded_years >= 3`。
- **Research targets：無，固定為 `{}`。** 不把 gate 外的診斷寫成資格目標。
- v005 preregistration 也會記錄既有的 Historical Evaluation gates（12 項），但本派工不執行正式 Historical Evaluation：base compounded return > 0、base PF > 1.10、completed trades >= 20、family-wise confidence >= 0.90、maximum fold positive-profit concentration <= 0.50、maximum fold trade concentration <= 0.50、maximum realized trade-loss fraction <= 0.04、positive traded-fold ratio >= 0.60、stress max drawdown <= 0.10、stress PF > 1.00、stress return > 0、traded folds >= 3。
- 固定 `initial_cash=100000`、`maximum_holding_sessions=11`、`fold_warmup_sessions=25`；成本、持有與風控值逐項沿用 v009。Block bootstrap diagnostics 固定 block lengths `[3,5]`、50,000 repetitions、seed `20260902`、每種 block length 使用相同 seed。

## 預期程式與 synthetic-only preflight

- 預計增加一個 Candidate adapter：`src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_sma20_sma50_regime_v001.py`，計算 20／50 日均線並只對 v009 原始訊號套用 strict regime predicate；所有其他交易函式和設定沿用 v009。Control 直接呼叫 v009 `DEFAULT_SPEC`。Development runner 產生同格式 candidate／baseline evidence；runner contract 標為 `synthetic_only: true` 供 v005 隔離 preflight 使用。
- preflight fixture 至少覆蓋：有原始 v009 訊號且 SMA20>SMA50 時 Candidate/Control 均接受；有原始訊號但 SMA20<SMA50 時只有 Control 接受；相等時 Candidate 拒絕；SMA(50) 尚未就緒時不得放行；只改變訊號日之後的 synthetic bars 不得改變該訊號日均線或 predicate；filter 通過時持倉成交、退出、風險與成本等欄位遵守相同 v009 contract。
- `prepare` 會執行 v005 隔離 synthetic runner preflight；預計 contract 同時提供 synthetic Development 與 workflow 要求的 synthetic-only runner contract case，不載入正式評估資料、不產生正式 Evaluation/Terminal evidence，也不執行 challenge、replay 或 freeze。此 preflight 只能在 PM 明確核准 checkpoint 後執行。

## Digest cross-bindings 與核准停點

- 已計算且核對的固定輸入：assignment canonical digest `308a2b80aa35521c16cd4b50173f5c274d276c0e0fbddf512aa81ec2f3ce3f8b`；workflow reference canonical digest `40396c0c742a653a589c5bfb738358149ae7c4302e55dc732362975902af3b90`；Data CSV SHA-256 `a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7`。
- 完成 source 與設定檔後，`source-bundle.yml` 逐一列出候選 adapter、固定 v009 source、runner、runner contract、資料取得／snapshot metadata、preregistration、qualification spec 及各自 canonical SHA-256；其 manifest canonical digest 綁進 trial inputs。
- `preregistration.yml` 會先以 canonical YAML 固定假說、唯一候選、Control、gates、targets、成本與交易設定。Create plan 內嵌的 preregistration 必須重算為同一 digest；Development `inputs.yml` 會 cross-bind exact `study_id`、trial ID、preregistration digest、source-bundle digest、資料路徑及資料 digest；candidate／baseline publication 再精確綁定 inputs 與兩份 evidence envelope digest。source 或 prereg 任何內容變動都必須重新計算所有下游 digest，不能沿用舊值。
- 本階段尚未產生正式 `preregistration.yml`、`source-bundle.yml`、Trial inputs digest 或 source file digests，也沒有 Study 目錄或 workflow operation。待 PM 核准設計後，才落實完整檔案、重算上述 digest cross-bindings，並再次交付可核對的 prepare-before checkpoint；未收到 PM 明確批准前不呼叫 `prepare`、`create`、Development 或 runner。

## 權限邊界

目前只檢查了 v005 workflow 定義、assignment、v005 Study 設計 manifest、v009 strategy source，以及允許的 TSM warmup+Development CSV。未讀取 `historical-evaluation-artifacts/`、`.super-admin/`、quarantine 或 Historical Evaluation/Terminal 證據；未執行 Lifecycle operation、runner 或正式評估。
