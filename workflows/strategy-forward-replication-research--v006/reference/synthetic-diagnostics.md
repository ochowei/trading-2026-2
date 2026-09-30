# 原生合成診斷與完整契約

診斷的目的，是先證明人造價格確實能形成已登記條件，再核對策略如何接受與拒絕訊號。它沒有研究績效、候選資格或發布授權效力；完整 precreate、runner 檢查與資格門檻仍然必須通過。

## 均線契約與暖機

見 `examples/sma-regime-implementation-contract.example.yml`。`indicator_contract.regime` 固定 `kind: sma-comparison`、`input: Close`、`operator: '>'`，明列含當日收盤與未就緒拒絕；fast／slow 各有完整 lookback、min_periods 與實際輸出欄位，另有允許欄位。候選 `signal.regime` 和事前登記 `eligibility_rules.accepted_signal.regime` 必須與它一致。

視窗必須完整暖機，fast 短於 slow。目前內建案例支援一般均值回歸、RSI、量先行、收盤反轉加這個均線比較。其他 operator、輸入欄位、不完整視窗或 ATR 狀態機加 regime，要回報不支援，不能退回不包含條件的通用資料後宣稱通過。

原生暖機取全部指標的最長邊界：SMA／ATR／Bollinger 為 min_periods−1，RSI 為 min_periods，量先行為 average_min_periods+lead_min_periods，regime 的兩個視窗也各納入。SMA50 的 required history 是 49；登記與引擎的 fold warmup 小於 49 就拒絕。不得自動修改候選常數來修補這個拒絕。

## 真實計算與拒絕分類

| 診斷 | 實際意思 | 下一步 |
| --- | --- | --- |
| `synthetic-contract-unsupported` | regime 未明示，或內建案例無法完整理解該條件 | 補完整契約，或由維護者另設能驗證此語意的案例 |
| `synthetic-fixture-invalid` | 價格形狀沒有形成必要的真實 raw signal | 修正人造資料，保留策略與門檻 |
| `synthetic-implementation-invalid` | 指標值、raw／accepted、持有、冷卻或成交違反契約 | 由開發者修正實作後重新準備 |
| `synthetic-binding-invalid` | Source Bundle、契約、引擎或其 bytes 指紋不一致 | 重新核對原來源與全部相依程式 |
| `fold-warmup-too-short` | 最長指標尚未就緒，登記就已允許訊號 | 由開發者依派工處理候選／暖機契約；不能只把 seed 往後移 |

原生 guard 直接從 Close 重算長短均線，並完整比較允許欄位與 raw signal。它保留均線相等、尚未就緒、錯誤指標、缺少 raw、無接受訊號、錯誤冷卻與錯誤持有的拒絕。Control 對照使用同一價格與未加 regime 的 v009 引擎；Control 成功不能替代候選的原生結果。

## 來源、Schema 與報告

`source-bundle.schema.yml` 驗證來源清單，`implementation-contract.schema.yml` 驗證完整規格，`synthetic-report.schema.yml` 要求 Workflow、Source Bundle、完整契約、原來源、引擎、spec／cost 常數與報告內容的 digest（內容指紋）。Source Bundle 內每個來源先核對 bytes，再載入引擎；受限資料、CSV、重複路徑或漂移不能進入合成檢查。

`_find_contract` 回傳的來源標籤，決定 external、candidate 或 preregistration 的原檔。保留 implementation_contract、indicator_contract 與 eligibility_rules.indicator_contract 內嵌形式。凍結 manifests 的同 bytes 副本，仍綁原 research 路徑；副本漂移則拒絕。本版新 Study 的完整 precreate 仍要求唯一 external contract，內嵌相容性只保存既有唯讀診斷能力。

`prepare_checks: passed` 的 runner report 另須完整 `native_synthetic`，不能只寫成功旗標。prepare 與隔離 consumer 都由原生 precreate 產生它；建立前會重跑完整原生 guard 並比對完整報告。Workflow 維護者的開發檢查只測 report Schema、綁定與原生函式，涉及隔離 consumer 建立／發布的完整 runner 路徑留給 Workflow 執行者。

## 可直接執行的人造示範

以下命令在 Repo 根目錄執行。將 `/tmp/v006-sma-demo` 換成尚不存在的 Repo 外路徑；工具會建立人造設定與公開 Package 定義副本，沒有 Study、event、authority 或 Workflow Release。

```sh
task037_package=workflows/strategy-forward-replication-research--v006
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python "$task037_package/tools/build_synthetic_demo.py" \
  --directory /tmp/v006-sma-demo
PYTHONPATH="$task037_package" PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  -m operations.synthetic_diagnostics --repository-root /tmp/v006-sma-demo \
  --study-id synthetic-regime --report /tmp/v006-sma-diagnostic.yml
PYTHONPATH="$task037_package" PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  -m operations.legacy_checks --repository-root /tmp/v006-sma-demo precreate synthetic-regime
```

兩項診斷均應退出 0，原生 precreate 沒有 warnings。診斷報告只寫在 Package 外；重複寫入相同 bytes 可重驗，異內容不得覆寫。

要重現固定 25 日暖機的真實拒絕，另外建立新目錄：

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python "$task037_package/tools/build_synthetic_demo.py" \
  --directory /tmp/v006-sma-short-warmup --original-warmup
PYTHONPATH="$task037_package" PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  -m operations.legacy_checks --repository-root /tmp/v006-sma-short-warmup precreate synthetic-regime
```

第二項應退出 1，包含 `fold-warmup-too-short`；synthetic 子檢查依新價格可通過，完整 precreate 仍然失敗。這個結果證明新案例沒有豁免正式契約。
