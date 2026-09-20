---
name: build-strategy-study-v003
description: 以既有明確派工建立或接續 v003 Development Study 至候選凍結；Study 只提供標準化 engine interface，由 Workflow Package 的共用 Development runner 執行。
---

# 角色與範圍

目前角色須為 **study 開發者**，不自行切換角色。先讀取根目錄 `AGENTS.md` 與本 Workflow Package 的 `reference/operations.md`。本 skill 只處理 `development-to-freeze`，不執行 Historical Evaluation、Terminal、challenge 或 Replay。

正式 Study 必須綁定有效的 Workflow Release，不能使用 `--allow-draft`。如果目前 Workflow Release 沒有同時提供下列能力，立即停止並回報 `workflow-capability-missing`，不得在 Study 內自行補一份 runner 或複製 validator：

- 由 Workflow Package 擁有的固定 Development runner；
- 版本化的 `development-engine` interface；
- 公開的 Development recomputation API；
- preflight 對 runner 重複率與相容欄位的硬性檢查。

Active Workflow Package 的修改必須依 Workflow Lifecycle 建立新版本、重新測試與重新發布；既有 Study 綁定的 Workflow、Source Bundle、runner 與 evidence 不得回寫或遷移。

# Study 與 engine 的責任邊界

Study Source Bundle 只保存研究本身需要的策略 engine、直接依賴、engine 測試、`implementation-contract.yml`、研究設定、`pyproject.toml` 與 lockfile。新的 Study 不得提供自己的 `run_development.py`，也不得把完整 Development runner、資料讀取、交易配對、metrics、bootstrap、gates 或 canonical evidence 序列化邏輯放進 Source Bundle。

`implementation-contract.yml` 必須宣告固定的 `development-engine-v1` interface，至少包含：

- engine path；
- candidate spec 與 baseline spec 的名稱；
- `backtest()` 的名稱；
- base cost 與 stress cost 的名稱；
- 若需要，`validate_bars()` 的名稱。

engine 的標準行為如下：

- `backtest()` 只接收 Workflow runner 傳入的 bars、spec、cost 與固定日期控制，回傳標準化的交易結果；
- 結果必須能提供 signal、entry、exit、shares、executed prices、fees、exit reason 與 held sessions；
- candidate 與 baseline 必須使用同一份資料、成本、執行規則與日期範圍，差異只能來自事前登記的 spec；
- engine 不得讀取 Workflow validator 的私有函式，不得連網、下載資料、寫入輸出目錄以外的檔案或自行讀取 preregistration 來決定研究規則。

candidate／baseline ID 由 preregistration 與 trial inputs 綁定，不在 engine 或 runner 內硬編碼。`backtest()` 的具體 Python 名稱可以不同，但必須由 contract 宣告，不能靠檔名或猜測解析。

# 共用 Development runner

Development 一律由 Workflow Package 提供的固定 runner 執行。runner 負責：

1. 讀取 request 指定的固定 OHLCV 與 `data_digest`，再次確認資料、preregistration、source bundle 與 trial inputs 的 digest；
2. 載入 contract 指定的 engine，分別執行 candidate／baseline 的 base 與 stress backtest；
3. 配對 base／stress 的交易生命週期，並拒絕兩者不一致；
4. 從 raw trades 計算 metrics、signal-year breakdown、leave-one-year-out、bootstrap、formal gates 與 disposition；
5. 輸出 canonical Development envelope，且必須同時包含 `candidate` 與 `baseline`。

runner 可以呼叫 Workflow 公開的純計算 API 產生 metrics 與 gates，但不得信任 engine 或 caller 自報的 pass、metrics、gates 或 disposition。`operations.publication` 與 validator 仍須從 frozen raw evidence 再次重算後才發布 Trial；不能繞過這條路徑直接寫 Event 或 evidence。

Historical Evaluation 如仍由 Study-specific runner 執行，必須與 Development runner 分離，並由 `run-strategy-evaluation-v003` skill 管理。本 skill 不得因 Development 重構而自行執行或修改 Historical Evaluation runner。

# 公開 recomputation API

不得 import 或呼叫 `_recompute_development` 這類私有符號。共用 runner 只能使用 Workflow Package 文件明確列出的公開 API，例如 `recompute_development()`。

這個 API 必須可重現，是沒有檔案 I/O、網路或副作用的純重算函式；輸入只包含 raw Development trades 與 frozen preregistration／rules，不能把 caller 已填好的 metrics、gates 或 disposition 當成計算依據。無交易、bootstrap 設定不一致、交易生命週期不合法或 gate 無法重算，都必須明確回報失敗或不可估計，而不能補填通過值。

若已發布的 Workflow Package 尚未提供公開 API，停止 prepare／development，回報缺少 Workflow capability；不得在 Study runner 內複製 `_recompute_development` 的實作。

# Runner 重複與相容欄位檢查

skill 的文字要求不能取代工具檢查。建立新 Study 前，必須確認 prepare／preflight 報告已通過：

- 新 Study 沒有自訂 Development runner；
- 若存在過渡期 adapter，與 Workflow common runner 的正規化程式結構（AST）／語法單位（token）相似度不得達到或超過 90%；
- 相似度達 90% 或以上，或 adapter 自己包含資料讀取、交易配對、metrics、bootstrap、gates、canonical evidence 序列化等共同流程時，必須刪除 adapter，改用 Workflow common runner；
- preflight 若尚未提供這個硬性檢查，不能以人工目測或 skill 提示宣稱通過。

如果保留 `volume_lead_*` 或其他舊名稱作為相容欄位，`implementation-contract.yml` 必須逐欄說明：舊欄位名稱、對應的標準欄位、實際用途、由 engine 或 Workflow 哪一層讀取，以及預計移除版本。沒有明確用途的欄位不得因 copy-forward 而保留。相容欄位不得讓 Workflow runner 直接依賴策略 engine 的私有命名；應由 engine contract 或 adapter mapping 吸收。

# 執行與恢復

保存使用者已給定的 Study、角色與 `development-to-freeze` 派工原文或可追查摘錄，不請使用者另外簽核。缺少實際範圍、研究決策、provenance 或 Workflow capability 事實時才補問；不得虛構指派者、verified-clean、interface 通過或未接觸結果。

依固定版本 CLI，以明示 `--role 'study 開發者'` 執行 `prepare`、`create`、`development`、`freeze-readiness`、`freeze`，或使用共用驗證的 `develop-to-freeze`。所有寫入提供 `--assignment`；原 plan、source、authority、Workflow digest 與 engine digest 不可因結果更換。

Development 若已有 `started` 記錄但沒有完整輸出，不得刪除輸出、換 runner、換 plan 或重新跑成另一個 Trial；依同一 operation、相同 inputs 與相同 assignment 恢復，必要時交由流程判定 evidence-unavailable／indeterminate。

candidate-frozen 即完成本階段派工，交接 Study ID、Workflow version、authority、事件 head、engine contract digest、Development evidence digest、候選資格與實際缺件。status 的 `not_inspected` 不能宣稱完整語意驗證。不得因 Development runner 通過而自行呼叫 Historical Evaluation。
