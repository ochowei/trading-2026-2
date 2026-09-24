---
name: study-development-note-authoring-v005
description: 為 strategy-forward-replication-research--v005 的單一 Study 撰寫約 300–600 字 Development 成果卡；只用 Development 證據，分清 gates、research targets、證據有效性與凍結資格／狀態，不接觸正式評估結果。
---

# v005 Development 成果卡

只處理使用者指定的一個 v005 Study。成果卡是 Development 證據的補充說明，不是 evidence、event、authority checkpoint、blind review 或 Historical Evaluation。撰寫者須是 **超級管理者** 或 **study 開發者**；不得代替其他角色執行 Study Lifecycle 或正式評估。

## 證據範圍

先確認 `AGENTS.md` 的角色與資料限制；若正式 Evaluation／Terminal outcome 曾被讀取，或接觸範圍不明，停止撰寫，不以「沒有找到結果」推定未執行。依 v005 `reference/operations.md` 與 `reference/workflow-reference.md`，先驗證 Study 的 `manifests/workflow-reference.yml` 確實綁定 v005 的 repository-relative Workflow package 及其 digest，再讀 Source Bundle 或 Development 證據。v005 不會把 Workflow 複製到 Study 的 `runtime/workflow/`；不得沿用 v004 的路徑假設。

只讀完成成果卡所需的 preregistration、候選 family、Development 計畫與 Trial inputs、Source Bundle 綁定的策略程式和設定、Development provenance，以及每個 Trial 的 candidate／baseline evidence、publication、runtime manifest 與 selection evidence。runtime manifest 只用來核對 `stage: development`、workflow/source/request/input/output 綁定及 `execution_workspace: temporary`；不要進入隔離暫存空間搜尋其他資料。可參照 v005 的 `reference/minimal-executable-study.md`、`reference/multi-asset-input.md` 和相應 evidence schemas。不得開啟、搜尋、雜湊、複製或引用 `historical-evaluation-artifacts/`、Historical Evaluation／Terminal evidence、quarantine／評估資料、`study.yml`、events、journals 或 Git 歷史；不得執行 Lifecycle、runner 或評估命令。

## 判讀規則

- **正式 gates 與 research targets 分開寫。** 只將 preregistration 和 Development evidence 可核對的必要 gate 列為 gate；研究目標另列其觀察結果。不得把 target-only 未達說成 gate fail，也不得用 Development 表現宣稱正式 Historical Evaluation 通過。若規則、結果或綁定不足，標示「尚不能判斷」。
- **證據有效性與績效分開寫。** 核對 `development-envelope` 是否同時有 candidate、baseline，evidence 是否標為 development、網路存取是否為 false、publication 是否以 digest 綁定輸入與輸出，以及 preregistration、Source Bundle、Trial、資料和選擇引用是否一致。以已保存的驗證結果或允許範圍內的 exact binding 判斷；不可只憑 evidence 自稱 pass。合法的績效 fail（包括沒有交易）仍可能是有效研究證據；無交易時不捏造統計值。
- **凍結資格不等於凍結狀態。** 資格依完整候選 family／trial registry、預先登記的 eligibility 與 selection 次序、candidate／baseline 證據、provenance、綁定完整性及漂移規則判斷。若允許的 Development publication 與 selection evidence 無法確認完整候選 family／registry，標示「尚不能判斷」，不得讀取 events 補足。freeze-readiness 或 selection evidence 只能支持資格／選擇判讀，不能單獨證明已凍結；狀態只在允許的 Development-only 紀錄有明確凍結佐證時才寫「已凍結」。否則寫「尚不能判斷」，不得讀取禁止的 Study 狀態資料補足。
- **遵守 v005 資產綁定。** 依 Development plan 判定使用舊式單資產 `data_path`／`data_digest`，或 `data_assets`；不得同時假設兩種契約。多資產時逐一保留 `asset_id`、`use`（trade／reference）、provider、symbol、各檔 digest 與期間，核對 Trial inputs 和 publication／runtime binding；清楚區分逐檔 digest 與資產清單 digest。不得把參考資產說成交易標的，也不得開啟 CSV 價格內容。

正文使用繁體中文、白話文，約 300–600 字；最多整理三個發現、兩個限制和一項可否證的下一輪變更。逐項標出「已確認」、「可能原因」或「尚不能判斷」；可能原因須明確保留為推測，不能寫成已證實因果。結尾列出實際使用的 Development-only 來源及讀取邊界，不聲稱知道正式結果。

預設直接在對話輸出。只有使用者明確要求寫檔且指定目標路徑時才寫入；目標已存在時只 append，不覆寫；無法安全追加時停止並回報。不得修改 Workflow、Study、manifest、evidence、event、authority 或正式結果。
