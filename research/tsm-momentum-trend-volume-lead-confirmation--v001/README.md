# TSM 動能趨勢＋量先價行 v001

本目錄是 `tsm-momentum-trend-volume-lead-confirmation--v001` 的單一研究 bundle，對應 workflow `strategy-forward-replication-research--v001`。

## 假說

在未下彎的 SMA(20) 順勢狀態中，若當日成交量至少達到前 20 個已完成 session 平均量的 1.10 倍，成交量先發出動能可能擴張的訊號；策略不在事件日進場，改在事件後第 1–5 個 XNYS session 等待收盤高於前一 session 的價格確認。確認後下一個 XNYS open 做多。事件跌到事件收盤的 85% 以下即失效，五個 session 後過期，新未確認事件取代舊事件。

所有指標在 session close 以當日及過去資料計算，進場使用下一個 session open；固定 4% stop、4% target、10 個完整持有 session、5 個完整 session 冷卻及 2% risk budget。沒有均值回歸超跌交易路徑，也沒有 v024 的原路徑加補充突破路徑。

## bundle 內容

- `candidate-definition.yml`、`preregistration.yml`、`qualification-spec.yml`：事前假說、門檻、baseline 與 freeze 條件。
- `implementation-contract.yml`：引擎與指標、資料邊界、執行與風控的唯一契約。
- `data-snapshot-acquisition.yml`、`data-snapshot-set.yml`：共用 immutable TSM market-data 的來源與各角色日期 view。
- `development-trial-inputs.yml`：Development 的固定資料、診斷與 digest 綁定；`development-trial-inputs-approved.yml` 是 workflow schema 相容的發佈副本。
- `run_development.py`：只讀 2013 warmup 與 2014–2018 Development，禁止網路與正式 Evaluation 輸入。
- `run_historical_evaluation.py`：只保存 candidate freeze 後的接手 runner；本任務不執行。
- `event-payloads/`、`evidence/development-authorization.yml`：由 guarded writer 使用的 canonical payload 與 Development scope authorization。

## Development 交接狀態

Development trial 已按固定規格完成，evidence 位於 Study 的 `evidence/development.yml`，並已由 `trial-recorded` 綁定。48 筆交易下 formal Development gates 未通過，因此 candidate freeze 不具資格；research targets 另行記錄且均已觀察到。不得以這次結果調參或在同一 Study 內重跑。

本目錄與 Study 只保存 Development 階段資料。正式 Historical Evaluation 尚未執行，本任務也沒有讀取、搜尋或引用 `historical-evaluation-artifacts/`。
