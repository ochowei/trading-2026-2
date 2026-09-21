---
name: blind-review-strategy-study-v004
description: 對 strategy-forward-replication-research--v004 的單一 Study 做盲檢討，只使用研究設計、程式與 Development candidate／baseline 證據，不讀正式 Evaluation 或 Terminal 結果。
---

# v004 Study Blind Review

目前角色必須是 **超級管理者** 或 **study 開發者**。只檢討使用者明確指定的一個 v004 Study，不自行挑選、比較或建立 Study，也不重跑 runner。

## 盲性與讀取範圍

先讀 `AGENTS.md`，核對目標 Study 與本次對話的 outcome exposure。若已接觸正式 Historical Evaluation evidence、帶 outcome 的 terminal 或正式結果內容，停止盲檢討；不能假裝忽略已知結果。僅知道階段名稱、日期或 digest 不等於知道結果；曝光事實不明時不得猜測。

先解析 Study 的 `manifests/workflow-reference.yml`，驗證 v004 package、release／digest 與 policy binding，再依 reference 讀取：

- preregistration、candidate family、qualification／implementation contract 與 Development 設計；
- 每個已登記 Trial 的 Development candidate／baseline evidence、inputs、publication 與 digest；
- Source Bundle 明確綁定的研究程式、runner、測試與 Development data metadata；
- Development provenance、selection 或 assignment，只作補充，不反推正式事件已完成。

禁止開啟、搜尋、雜湊、複製或引用 `historical-evaluation-artifacts/`、正式 Evaluation／Terminal、quarantine／full evaluation data、`events/`、`journals/`、`operations/`、`study.yml` 或 Git 歷史。不得用完整 `status`／`validate` 取代本 skill 的盲讀範圍。

## 判定與輸出

逐 Trial 區分 formal gates、research targets、candidate／baseline evidence validity、candidate freeze eligibility 與盲性狀態。target 失敗不可改稱 formal gate 失敗；缺 evidence 只標示 unavailable，不推定未執行。blind eligibility 依實際 outcome exposure 判定，不把「尚未執行 Evaluation」當成唯一條件。

輸出繁體中文的已確認問題、影響、證據強度、限制與下一輪可否證建議，聲明未使用正式結果。預設只在對話輸出；只有使用者明確要求且指定不存在的新路徑時，才新增編號 review 檔，不覆寫既有檔案，不修改 Study、Workflow、authority 或 evidence。
