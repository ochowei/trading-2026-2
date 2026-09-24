# v005 多資產資料契約（Draft）

v004 的 Development 計畫只有一個 `data_path` 與 `data_digest`，隔離 workspace 只複製一個 `bars.csv`。Source Bundle preflight 排除 CSV，runner 合成契約也只產生一份六欄資料。因此 TSM 與 SOXX 無法在同一次正式 Development 中被逐檔核對。v005 新增 `data_assets` 陣列；既有單資產欄位保留供舊式單資產 Study 使用。兩種寫法不可同時出現。

## 每份資料如何固定

`data_assets` 須有 1 至 16 筆，按 `asset_id` 排序且不得重複，恰好一筆為 `use: trade`，其餘為 `reference`。每筆包含 `asset_id`、`use`、`provider`、`symbol`、`data_path`、`data_digest`、`start_date`、`end_date`、`timezone: America/New_York`、`available_at: after-close` 及 `interval_role`。Development 的 role 固定為 `warmup-development`；Historical Evaluation 固定為 `historical-evaluation`。路徑須在 repository 內，不能穿越或解析進受限目錄；來源程式仍由 Source Bundle 分別鎖定。資料檔不混入 Source Bundle，而以 Trial inputs、operation plan、逐資產 access record、runner request、runtime manifest、candidate／baseline evidence binding 及 publication manifest 鎖定。

例如 TSM／SOXX 案例，可將 TSM 設為交易標的、SOXX 設為參考資產；若再加第三條參考指數，只需增加一筆具有獨立 digest 的資料。實際 Study 必須在事前登記使用哪個資產、訊號公式與可得時間，不能在見到結果後更換參考指數。

所有資產都使用 XNYS 交易日、紐約時區及 `Date,Open,High,Low,Close,Volume` 六欄。每一檔的日期需嚴格遞增、沒有重複或缺少交易日；不同資產的日期清單必須完全一致。缺值、非有限數字、非正價格、負成交量、日期越界、digest 漂移或日曆不一致都拒絕，不會前填、插值或自動取交集。單檔上限 32 MiB／10000 列，總量 128 MiB。收盤資料於該日收盤後才可得；當日資料最早只能決定下一個交易日的進場。runner 必須以此規則實作，preflight 與研究程式審查須核對，不能單憑 request 字段推定無前視。

Development 只接受固定 warmup／Development 日期，拒絕 quarantine 或 Historical Evaluation 資料。Historical Evaluation 資料僅由指定評估角色依已凍結的 snapshot 與相同資產清單讀取。凍結前，snapshot 的每個資料角色都要列相同的資產 ID、用途、來源與標的；每一角色的 `data_digest` 是其逐資產清單的 canonical digest。此值和 Evaluation plan 的 `data_digest` 必須一致，每份 CSV 仍以自己的 digest 驗證。正式 Evaluation 只能由另一角色依 Lifecycle 執行；本 Draft 不包含任何正式結果。

隔離 runner 只看到 `run/assets/<asset_id>.csv`、固定 request、Source Bundle 程式及 Workflow Package。永久 runtime 保存 request、manifest 與 evidence 引用，不保存 CSV。runner 從 `data_assets` 讀取每一筆並核對 digest；`availability_policy: after-close-next-session` 明示可得時間。單資產舊 request 仍保留 `data_path: run/bars.csv`。

## 驗證與交接

此 Draft 的合成 preflight 分別以一、二、三個資產做 Development runner、candidate／baseline 與發布路徑驗證；測試另外拒絕重複 ID、缺檔、digest 漂移、日期缺漏或錯位、受限路徑／日期、資源上限與與凍結輸入不一致。Workflow 執行者形成 Release Candidate 前，仍須依 `IMPLEMENTATION-PLAN.md` 補做全部 schema、政策、狀態轉換、Evaluation 多資產端到端、必要 pytest 與 Ruff，產生可重算 manifest 與 test report。只有 Trusted Approver 建立有效 `release.yml` 後才可供新 Study 使用。
