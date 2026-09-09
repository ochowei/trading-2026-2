---
name: study-development-note-authoring
description: 為 strategy-forward-replication-research--v001 的單一 Study 撰寫 300–600 字 Development 成果卡；只限超級管理者與 study 開發者使用，嚴格禁止讀取正式 Historical Evaluation 結果與 historical-evaluation-artifacts/。
---

# Study Development 成果卡撰寫

## 目的

使用同一份短格式，記錄單一 Study 在 Development 階段實際驗證了什麼、出現什麼結果、哪些解釋仍只是推論，以及下一個 Study 應只測哪一件事。成果卡必須如實區分完整、gate 失敗、部分完成、證據不可用與資料不足，不能把補充性筆記寫成正式結果。

這是一份給人閱讀的研究摘要，不是正式 evidence、Study Event、`study.yml` 或正式結果的替代品。每次只處理一個 Study，不自行比較或合併多個 Study。

## 角色限制

- 本 skill 只能由 **超級管理者** 或 **study 開發者** 使用。
- 執行任何讀取前，必須確認目前對話角色是上述其中之一；角色不明時先停止並請使用者指定角色。
- 其他角色不得使用本 skill，也不得透過它讀取 Study 或寫入成果卡。
- 超級管理者原本擁有較高的檔案權限，但不能用這個 skill 解除下列資料隔離規則。

## 絕對禁止讀取的內容

- 絕對不可開啟、搜尋、雜湊、解析、複製或引用 `historical-evaluation-artifacts/` 及其任何子目錄或檔案。
- 為避免從其他位置繞過隔離，也不可讀取任何正式 Historical Evaluation、Terminal Evidence、正式交易明細或正式結果報告；包括檔名含 `historical-evaluation`、`terminal-evidence`、`terminal` 或 `evaluation-report` 的檔案。
- 不可讀取目標 Study 的 `study.yml`、`events/`、`journals/` 或可能包含正式 outcome 的摘要，以免從投影或事件鏈側面得知後段結果。
- 不可執行會遞迴掃描整個 repository 的 `find .`、未限制路徑的 `rg`、`git grep` 或類似指令。只使用明確列出的允許路徑。
- 若使用者在本次對話中已提供目標 Study 的正式結果、交易、指標、年度表現或失敗 gate，必須停止；不能假裝自己仍處於盲讀狀態。

## 允許讀取的內容

只可依需要讀取下列與指定 Study 直接相關的資料：

- `workflows/strategy-forward-replication-research--v001/studies/<study-id>/manifests/` 下的 preregistration、candidate definition、qualification spec、implementation contract、source bundle、Development inputs 與資料快照清冊。
- 目標 Study 的 Development evidence、`evidence/development.yml`、Development authorization，以及其明確引用的 Development 輸入；`evidence/development.yml` 必須存在、可讀且被允許的 Development validator 接受，才能做數值或 gate 分析。
- `research/<study-id>/` 下的研究規格、Development runner、Development evidence、程式與測試；不可讀取該目錄的正式 Evaluation、Terminal 或可能包含後段結果的 README。
- `src/` 與 `tests/` 中由 Development source bundle 或使用者明確指定的策略程式與測試。
- 與本次 Study 直接相關、且明確聲明沒有讀取正式 Evaluation 或 Terminal 結果的盲檢討文件。
- 本 skill 同目錄的 [`study-outcome-note-template.md`](study-outcome-note-template.md)。每次撰寫前都要先讀完它。

不得用 `/tmp` 原始輸出、相似檔案、正式結果或其他未列入白名單的資料補齊缺口。

## 成果卡狀態判定

成果卡的 `成果卡狀態` 只能使用以下值：

- `complete`：合法、可驗證的 Development evidence 存在，base 與 stress 的結果完整，且 Development gate 通過。
- `failed`：合法、可驗證的 Development evidence 存在，必要結果完整，但 formal Development gate 失敗。
- `partial`：只完成部分 Development 情境，或已確認部分資料產出而其餘部分未完成；若某一側明確未執行，仍屬部分完成。
- `evidence-unavailable`：`evidence/development.yml` 缺失、無法讀取或 validator 不接受，或必要 evidence 無法驗證。
- `indeterminate`：允許讀取的資料存在，但不足以判定完整性、gate 或其他狀態；不可用猜測補值。

先處理 `evidence-unavailable`：一旦 `evidence/development.yml` 缺失、無法讀取或 validator 不接受，立即停止數值與 gate 分析。仍可產出證據不可用版成果卡，但 Development/base 與 Development/stress 都必須寫「證據不可用」及已確認的原因與影響，不填零、不猜測、不重建數值。這種成果卡只是補充性 Development 筆記，不會改寫 Study lifecycle。

在 evidence 合法且可驗證時，只有 base 與 stress 都有完整結果且 gate 通過才是 `complete`；兩者完整但 gate 失敗才是 `failed`。一側明確未執行，或已確認只部分執行且部分資料未產出，寫 `partial`。若資料存在但無法判定是否執行、是否完整或 gate 狀態，寫 `indeterminate`。

若必要檔案不在上述白名單、內容是否含正式結果不明，或使用者要求讀取被禁止的資料，停止並說明限制，不要改用相似檔案猜測。

## 執行流程

1. 確認角色、repository 根目錄與唯一的 Study ID。Study 必須屬於 `strategy-forward-replication-research--v001`。預設直接在目前對話輸出成果卡，不要求也不猜測檔案路徑。
2. 在讀取內容前，先用明確路徑確認目標檔案存在；不要列出或掃描整個 Study 目錄。
3. 讀取模板，再依允許清單讀取研究問題、主要變更、`evidence/development.yml`、程式與必要測試；先確認 evidence 能被讀取與驗證，再決定是否可分析數值與 gate。
4. 只整理 Development 結果。結果表只填 `Development / base` 與 `Development / stress`：完整資料才填實際結果；明確未執行寫「未執行」及原因；必要資料缺失或無法驗證寫「證據不可用」及原因；資料存在但不足以判定寫「尚不能判斷」。三者不得混用。
5. 缺少或無法驗證 `evidence/development.yml` 時，停止所有數值與 gate 分析，改產出 `evidence-unavailable` 成果卡，只記錄已確認的證據缺口、影響與限制。不可用 `/tmp`、相似檔案、正式結果或其他未允許來源替代。
6. 把文字分成三種強度：
   - **已確認**：能由允許的 evidence 或程式／測試直接支持的事實。
   - **可能原因**：合理但尚未證明的解釋，需標明證據強度。
   - **尚不能判斷**：目前資料無法回答的問題。
7. `candidate_freeze_status` 只能依允許的 Development-only 資料判定：資料明確支持時寫「已完成」、「未完成」或明確記載的「不適用」；無法確認時寫「尚不能判斷」。不得讀取 `study.yml`、`events/`、`journals/`、Terminal Evidence 或正式結果推斷。
8. 提出一個下一輪方向：只允許一個主要變更，並寫出可事前判定的成功與否證條件。若 evidence 不可用，建議可改為修正證據產製或驗證流程，不得擅自調整策略參數。不得把建議寫成已證明有效，也不得在原 Study 上修改後重試。
9. 正文控制在約 300–600 字，最多 3 個主要發現、2 個限制、1 個下一輪方向；完整交易、參數與詳細分析留在允許的 Development evidence 或 review。

## 輸出與寫入限制

### 對話輸出（預設）

- 直接在目前回覆中輸出完整成果卡。
- 不建立檔案、不修改檔案，也不自行選擇或猜測輸出路徑。

### 寫入檔案（只有使用者明確要求時）

- 使用者必須明確要求寫入檔案，並提供完整且精確的目標檔案路徑；只提供目錄、檔名不完整或路徑含糊時，先請使用者補充，不進行寫入。
- 目標路徑不得位於 `historical-evaluation-artifacts/` 或其他被禁止的正式結果位置；也不得因為使用者提供路徑就修改 Workflow、策略程式、測試、manifests、evidence、events、journals、authority 或任何正式 artifact。
- 目標檔不存在時，才可依模板建立新檔。
- 目標檔存在時，先確認它是 Development-only 的成果卡集合，而不是其他文件或含正式結果的檔案。集合檔可以同時包含不同 Study 的筆記，不要求新舊 Study ID 相同。
- 確認可以合併後，保留原文，在檔案末尾以分隔線、記錄日期與新的 Study ID append 一個完整的新成果卡；不得覆寫、重排或刪除任何舊 Study 的內容。
- 若無法確認舊檔案的用途、Development-only 範圍或是否適合累積多個 Study，停止寫入並請使用者提供新的檔案路徑；不要為了 append 而猜測。
- 檔案編輯使用 `apply_patch`，保留既有使用者變更。
- 所有筆記與回覆使用繁體中文；`pass`、`fail`、`indeterminate` 等既有機器值可原樣保留，但要用白話說明實際意思。

## 完成標準

成果卡必須讓讀者在短時間內知道：本次研究問題、唯一主要變更、Development 的 base／stress 結果、已確認與未確認的地方，以及下一輪唯一建議。結尾附上允許讀取之規格、Development evidence、程式或測試的 repository-relative 連結；不得附上或引用任何被禁止的正式結果來源。預設成果卡出現在對話中；只有使用者提供精確路徑並明確要求寫檔時，才回報檔案寫入或 append 的結果。
