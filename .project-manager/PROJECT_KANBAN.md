# 專案任務看板

本看板用來讓專案管理者建立、分派、追蹤與驗收本專案的任務。

## 看板操作權限

以下權限只適用於本檔案，不會因看板而擴張任何角色對 `.super-admin/`、`historical-evaluation-artifacts/` 或 `.project-manager/` 其他內容的權限；`historical-evaluation-artifacts/` 的特別存取權限以 `AGENTS.md` 為準。若本表與 `AGENTS.md` 衝突，以 `AGENTS.md` 為準。

| 角色 | 看板操作權限 | 實際限制 |
| --- | --- | --- |
| **超級管理者** | 完整操作 | 可以讀取、建立、編輯、移動與驗收任務，也可以修改本檔案的權限與流程規則。 |
| **專案管理者** | 完整任務管理 | 可以建立任務並放入 TODO、指派負責角色、調整優先級、編輯任務內容、將任務移到任一欄位，以及驗收後移到 Done；不可修改本表的角色權限與流程規則。 |
| **Policy 管理者** | worker：讀取及更新已指派任務 | 可以處理自身 Policy 職責範圍內的任務，並將任務從 TODO 或 Pending 移到 Doing；不可將 Doing 移到 Pending 或 Done，也不可修改看板權限與流程規則。 |
| **workflow 維護者** | worker：讀取及更新已指派任務 | 可以處理 workflow 治理職責範圍內的任務，並將任務從 TODO 或 Pending 移到 Doing；不可執行 Lifecycle、將 Doing 移到 Pending 或 Done，也不可修改看板權限與流程規則。 |
| **workflow 執行者** | worker：讀取及更新已指派任務 | 可以執行自身被指派的 Lifecycle 任務，並將任務從 TODO 或 Pending 移到 Doing；不可將 Doing 移到 Pending 或 Done，也不可修改看板權限與流程規則。 |
| **study 開發者** | worker：讀取及更新已指派任務 | 可以處理自身 study 開發職責範圍內的任務，並將任務從 TODO 或 Pending 移到 Doing；不可將 Doing 移到 Pending 或 Done，也不可修改看板權限與流程規則。 |
| **Study 歷史評估執行者** | worker：讀取及更新已指派任務；可操作指定 artifact 資料夾 | 可以更新評估進度、備註與證據路徑，並將任務從 TODO 或 Pending 移到 Doing；不可將 Doing 移到 Pending 或 Done，也不可修改看板權限與流程規則。依 `AGENTS.md` 規定，可以讀取、寫入並 commit `historical-evaluation-artifacts/`，但不得覆寫或刪除既有 artifact。 |

### 狀態移動規則

- 專案管理者把新任務放入 TODO，並填寫負責角色、優先級與驗收條件。
- 被指派的執行角色接手任務時，將 TODO 或 Pending 移到 Doing，並在任務內記錄目前進度。
- 任務遇到阻塞或延期時，執行角色先在任務內說明原因；由專案管理者將 Doing 移到 Pending。
- 執行角色完成工作後，補上結果與驗證資訊；由專案管理者確認符合驗收條件後將 Doing 移到 Done。worker 不得自行將 Doing 移到 Done。
- Done 任務如需重新處理，只能由專案管理者或超級管理者重新開啟，並補充重新開啟的原因。

## 任務格式

每個任務使用遞增且唯一的編號，並至少包含以下資訊：

```markdown
### [TASK-001] 任務名稱
- **狀態**：TODO
- **優先級**：高／中／低
- **負責角色**：角色名稱
- **執行者**：subagent 或人員識別名稱
- **建立日期**：YYYY-MM-DD
- **更新日期**：YYYY-MM-DD
- **依賴／阻塞**：無
- **驗收條件**：完成後如何確認結果符合要求
- **摘要**：要做什麼，以及會帶來什麼影響
- **進度／備註**：目前進度、決策、阻塞原因或驗證結果
```

---

## 📋 TODO

> 已由專案管理者建立並排序，等待負責角色接手的任務。

（目前沒有 TODO 任務）

---

## 🔨 Doing

> 正由被指派的角色處理中的任務。

（目前沒有 Doing 任務）

---

## ⏳ Pending

> 因阻塞、依賴或等待決策而暫停的任務。

（目前沒有 Pending 任務）

---

## ✅ Done

> 已完成工作並由專案管理者驗收確認的任務。

### [TASK-001] 發想並建立全新的 TSM 動能趨勢與量先價行 Study 假說
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Sagan（subagent，study 開發者）
- **建立日期**：2026-09-17
- **更新日期**：2026-09-17
- **依賴／阻塞**：無
- **驗收條件**：
  1. 在 `.study-developer/development-note/TSM.md` 新增一張繁體中文 Development 成果卡，提出一個可被單一 Development trial 驗證的全新 TSM 假說；在實際 evidence 產出前，不得填入或推測交易結果、報酬、PF 或回撤。
  2. 假說必須以「可辨識的動能／趨勢狀態」為研究核心，並清楚定義「成交量先發生變化、價格之後確認」的先後順序、觸發條件、失效條件與避免未來資料外洩的規則；不得只是把既有 Study 改名或調參。
  3. 新 Study 必須使用全新的 Study／candidate 識別，並在卡片中說明它與既有 `tsm-mean-reversion-two-stage-volume-reversal--v024` 的實質差異；不得沿用 v024「在均值回歸原路徑上加上升趨勢放量五日突破補充路徑」的結構，也不得在同一 Study 內事後調參。
  4. 完成對應的 preregistration、candidate definition、implementation contract 與必要的 Development 輸入／測試規格，固定資料範圍、基準策略、進出場、成本、風險、持有期、冷卻期與事前 gates；確認符合 `strategy-forward-replication-research--v001` 的 Active workflow 與 Study 規範。
  5. 完成 Study preflight／結構與語義驗證，產出可供後續 Development 執行者接手的檔案路徑與驗證紀錄；工作在 Historical Evaluation 前停止，不得執行或引用正式 Historical Evaluation 結果。
- **摘要**：請 study 開發者在既有 TSM 均值回歸與 volume-lead 分支之外，設計一個真正以順勢動能為主體的研究假說。方向可聚焦於「趨勢先成立、量能先出現蓄勢或擴張訊號、價格再以收盤／突破確認」是否能捕捉動能延續，但具體指標、門檻與執行語義必須在事前登記中一次固定。這項任務的影響是建立下一個可審計、可重現且不與 v024 重複的 TSM 研究起點。
- **進度／備註**：2026-09-17 由專案管理者驗收通過。已核對新 Study `tsm-momentum-trend-volume-lead-confirmation--v001`、繁體中文成果卡、preregistration、candidate definition、qualification spec、implementation contract、Development inputs、策略引擎與測試；唯一性／workflow、precreate、authority staged、guarded writer、writer validate、diagnose 與 studyctl all 均有通過紀錄，新增 Study 單元測試 `9 passed`。Development evidence 有效但 formal gates 未通過，因此 candidate freeze 不具資格；這是研究結果，不影響本任務「建立可審計新假說並完成 Development 交接」的驗收。Study 停在 `trial-recorded`，未執行、讀取或引用正式 Historical Evaluation。
