# FXI 深度回檔、無 ClosePos、七-session cooldown 研究

這個目錄保存正式 Study 的 outcome-relevant 程式外研究規格。研究目的不是證明策略一定有效，
而是讓使用者提出的假說可以被一次性、完整且可重算地否證。

## 目前狀態

研究已取得並凍結完整 FXI 2013--2025 adjusted OHLCV 快照。快照正好涵蓋 3270 個 XNYS
sessions，沒有缺漏、額外 session 或空值。正式離線 Development 已完成並通過全部 gates：

- 29 筆完成交易，5 個有交易年度；
- base return `42.6419%`、profit factor `1.6903`；
- stress return `30.0023%`、profit factor `1.4784`、最大回撤 `14.5615%`。

Trial Registry 已凍結，研究擁有者的確認已保存為 `verified-clean` provenance evidence，唯一候選、
qualification spec、完整五角色 snapshot set 與 selection evidence 也已完成 Candidate Freeze。

2020--2024 Historical Evaluation 未通過，Study 已正式終止為 `fail`，本假說遭否證：

- 共 22 筆完成交易、5 個有交易年度，但只有 2022 年為正；
- base return `-42.2758%`、profit factor `0.4795`；
- stress return `-48.6446%`、profit factor `0.4285`、最大回撤 `51.1066%`；
- positive traded fold ratio 僅 `0.20`，唯一正報酬年度占全部正 profit 的 `100%`。

依預先登記的 sequential gate，失敗後不得執行或選報 baseline、random-entry、九項 challenge
或 2025 replay，也不得修改候選後沿用同一 Study 重試。

正式執行必須依下列順序進行：

1. 已完成：在 formal run 外取得 Yahoo `auto_adjust` FXI 日線，保存 2013--2025 五個固定角色
   的完整 XNYS session inventory 與 content digest。
2. 已完成：只開啟 2013 warmup 與 2014--2018 Development，以 base、stress 成本跑唯一 Trial。
3. 已完成：Development gates 全數通過，Trial Registry 已凍結。
4. 已完成：provenance audit 為 `verified-clean`，唯一 candidate 與全部 outcome-relevant inputs 已凍結。
5. 已完成：2020--2024 Evaluation 失敗，事件鏈已保存完整 raw trades、重算 metrics 與 terminal evidence。
6. 不執行：因必要 Evaluation gate 已失敗，九項 challenge 與 2025 replay 依法停止。

## 不可自行補上的結果

`preregistration.yml` 內的門檻與 challenge 定義都是事前規則，不是執行結果。沒有 immutable
snapshot、完整 trades/fills 與重算 evidence 時，只能維持 pending；不得手填 `pass`。

## 20-session 與 workflow 日期跨度

策略在下一開盤進場，進場 session 算第 1 個完整持有 session；若 target 與 stop 都沒成交，
第 20 個持有 session 收盤後，下一開盤退出。因此從訊號日到最晚退出日相差 21 個 session steps。
正式 preregistration 的 `maximum_holding_sessions: 21` 是既有 workflow 對 `signal_date` 到
`exit_date` 的結構上限；真正策略仍由 runner 與 evidence 嚴格限制為 20 個完整持有 sessions。
