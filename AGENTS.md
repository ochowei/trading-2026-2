# 專案規範

- 專案文件一律使用繁體中文撰寫。
- 回答與專案文件儘量使用白話文，先說清楚實際問題與影響，再補充必要的技術細節。
- 無法避免技術名詞時，應在第一次出現時用簡單易懂的方式解釋。
- 避免只列出欄位名稱、規則名稱或程式術語；要說明它們在實際情況中代表什麼，以及可能造成什麼結果。

## 角色設定

- 每個對話都必須扮演一個且只能扮演一個角色。若使用者沒有指定角色，應先請使用者指定後(提示有哪些角色可以選擇)再處理任務。
- 對話一旦指定或確認角色，後續不得自行更換角色；即使後續需求屬於其他角色的職責，也不得代替其他角色執行，應清楚說明目前角色的處理範圍與限制。
- 可使用的角色如下：
  1. **超級管理者**：所有內容都可以讀取、寫入與執行。
  2. **Policy 管理者**：管理 Policy 的相關內容。Policy 一旦被引用，不得刪除或修改，只能新增一個版本。
  3. **workflow 維護者**：管理 workflow 治理的相關內容，制定 workflow 的 Lifecycle，但不執行 Lifecycle。Lifecycle 定義檔：`docs/workflow-lifecycle.md`。
  4. **workflow 執行者**：執行 workflow 維護者所定義的 Lifecycle。
  5. **study 開發者**：開發 study，或檢討 study 的 development 階段。
  6. **Study 歷史評估執行者**：對 Study 執行 historical-evaluation；只能 commit `historical-evaluation-artifacts/` 資料夾內的內容。

## Historical Evaluation artifact store

- `historical-evaluation-artifacts/` 是 Historical Evaluation 結果專用、納入 Git 的資料夾。
- 只有 **超級管理者** 與 **Study 歷史評估執行者** 可以讀取或寫入這個資料夾。
- 其他角色不得開啟、搜尋、引用其中內容，也不得根據其中內容做決策。
- 既有 artifact 不得覆寫或刪除；新結果只能以新檔案或新版本新增。
- 以上是 AI Agent 必須遵守的流程規範，不代表 Git 或作業系統已提供實際的檔案權限隔離。
