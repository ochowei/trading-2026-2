# SMA20>SMA50 阻塞根因與人造重現

原通用案例沒有做出所需的長期上升趨勢，所以正確的 SMA 濾網拒絕全部候選訊號。單純把事件往後排，能讓 50 日均線就緒，卻仍不能讓短均線高於長均線。此外，v005 原生暖機推導沒有納入新增的 regime（策略適用環境濾網）；這會掩蓋 25 日登記與 50 日指標實際就緒的差距。

本次只讀公開 Workflow 定義、公開 `src` 與人造案例。沒有讀真實市場資料、TASK-036 的私有準備內容或任何正式 Study 結果。以下契約由公開 test fixture 重建，固定呼叫公開策略的 `DEFAULT_SPEC`，並非宣稱已驗證某份私有 Study 契約。

## 實際呼叫與就緒位置

`operations.service.prepare` 先呼叫 `run_precreate`；`run_precreate` 必須合併 `run_contract` 與 `run_synthetic`。後者由契約找出引擎與 spec，透過 `_call_indicators`、`_call_backtest` 呼叫真實計算函式。測試工具沒有注入訊號，也沒有依設定名稱選擇成功答案。v005 的 runner preflight 還會執行隔離 Study consumer，本次沒有執行它。

公開候選來源是 `src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_sma20_sma50_regime_v001.py`，SHA-256 為 `4d0f756827e137b673b2975d654696caeeabd0d46a9e1f44dfa2dae8f5d14888`。呼叫常數是 `DEFAULT_SPEC`／`BASE_COST`；RSI=2、短均線=20、量平均=20、量先行視窗=5、完整持有=10、冷卻=5。公開 `DEFAULT_SPEC.fold_warmup_sessions` 是 25。

v005 `_derived_history_sessions` 與公開基本指標契約只推得 index=25。新增 SMA50 含當日 Close，需到第 50 列，也就是從零起算的 index=49 才就緒；SMA20 則為 index=19。`required_history_sessions=49` 表示訊號日前已有 49 列完整歷史，不是把 49 列誤稱成 50 日均線。

## 原通用案例的數字

v005 `_make_bars` 先放平坦 Close=100，再將事件前一天改為 90、事件日改為 95，成交量事件放在前 5 列。v009 Control 是相同執行規則、沒有 SMA20>SMA50 濾網的公開引擎。

| 事件 index | 真實 SMA20 | 真實 SMA50 | 候選 raw／accepted | Control raw／accepted | 濾網拒絕原因 |
| --- | --- | --- | --- | --- | --- |
| 36 | 99.25 | 尚未就緒 | 0／0 | 1／1 | 長均線尚未就緒 |
| 49 | 99.25 | 99.70 | 0／0 | 1／1 | 短均線未嚴格高於長均線 |
| 57 | 99.25 | 99.70 | 0／0 | 1／1 | 同上 |
| 65 | 99.25 | 99.70 | 0／0 | 1／1 | 同上 |

raw 是指標形成的原始訊號，accepted 是套用持倉與冷卻後接受的訊號。上述候選 raw 就已為零，沒有「raw 被 backtest 拒絕」的 session；拒絕發生在 regime 濾網。不能把空的 rejected 列表當成沒有拒絕條件。

隔離原生 `_run_signal_case` 的 8 組搜尋及 `_run_holding_cooldown_case` 的 160 組搜尋均回報 `synthetic-fixture-invalid`。Control 在相同單事件資料有 1 個 raw／accepted，證明原始均值回歸與反轉條件可成立，差異來自長期均線條件。引擎與 spec 的呼叫正確；主要阻塞是人造價格形狀不足，另有暖機契約的驗證缺口。

## v006 的原生證據

新產生器先上升至事件附近，再有兩日回檔／反轉；進場後保留平台價格，以測完整持有與下一開盤 time exit。價格事件是建構提示，每一列的均線、raw 與 accepted 都由真實引擎決定。guard 還從原始 Close 獨立重算均線、嚴格比較與完整訊號，錯誤均線、相等時錯誤允許、忽略冷卻及錯誤持有均被拒絕。

預設人造案例最早事件 index=57，依 max(最長指標就緒、spec 暖機) 加 8 列推得；不是 TASK／Study ID 特判。第一筆於 index=58 開盤進場、index=68 開盤 time exit，完整持有 10 個 session。兩組獨立案例保留冷卻邊界：

| 人造事件索引 | 原始／接受／拒絕 | 實際邊界 |
| --- | --- | --- |
| `[57,72,74]` | 3／2／1 | 退出後第 4 步的 index=72 有 raw，因冷卻未完成拒絕；index=74 接受，index=75 開盤進場 |
| `[57,73]` | 2／2／0 | 退出後第 5 步的 index=73 有 raw 並接受，index=74 開盤進場 |

這兩組各有兩筆合法 time exit，保存在原生 `cooldown_boundary_cases`，帶人造 CSV 指紋、實際 raw／accepted／rejected、拒絕原因與完整交易。另一組 `[57,71,73]` 同時驗證第 3 步拒絕與第 5 步接受；名稱與文件不把第 3 步說成第 4 步。

## 可重現命令與交接

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  workflows/strategy-forward-replication-research--v006/tools/reproduce_v005_fixture.py \
  --repository-root .
```

工具只依 v005 發布定義清單複製公開定義與兩份公開引擎到 Repo 外暫存目錄，執行上述唯讀原生函式；完整數字另保存在輸出中的 `reproduction.json`。不掃描或複製舊 Study、runtime、evidence、authority 或 Workflow Release。重現成功的工具退出碼是 0；內含兩個 fixture-invalid 是要重現的結果。

新版本明列 SMA20／SMA50 契約後，最長就緒為 49，完整原生 precreate 必須拒絕 25 日 fold warmup，即使新價格讓 synthetic 子檢查通過。原 TASK-036 仍需 study 開發者依新的明確派工核對並重新準備暖機與候選契約；原候選參數固定時不能在本任務偷偷更改。測試中的 49 日 `ready_engine.py` 只另立人造對照規格，不修改公開候選、Policy 或正式 Study。
