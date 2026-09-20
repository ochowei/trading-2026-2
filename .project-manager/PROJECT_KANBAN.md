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

## 🔨 Doing

> 正由被指派的角色處理中的任務。

---

## ⏳ Pending

> 因阻塞、依賴或等待決策而暫停的任務。

（目前沒有 Pending 任務）

---

## ✅ Done

> 已完成工作並由專案管理者驗收確認的任務。

### [TASK-004] 在 v003 開發新的 TSM 動能趨勢 × 量先價行假說並撰寫成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：study 開發者 subagent `01a0bcc6-81c7-7892-a1e6-32b5f9af7160`
- **建立日期**：2026-09-20
- **更新日期**：2026-09-20
- **依賴／阻塞**：無；v003 Workflow Release 已存在且為 Active
- **驗收條件**：
  - 先盤點 `.study-developer/development-note/TSM.md` 與既有 Study，明確證明新假說的動能、趨勢與量先價行機制不是既有規則的重複或只改版本號。
  - 依 v003 `development-to-freeze` 建立一個新的 Development Study，完成 preregistration、candidate／baseline、implementation、runner、data bindings、唯一 Development trial、evidence validation，以及規則允許的 freeze-readiness／freeze 嘗試。
  - 只執行 Development，不得執行 Historical Evaluation、Terminal、challenge 或 replay；既有 Study、既有 evidence 與既有成果卡不得覆寫或重排。
  - Development 完成後，依 v003 成果卡規範，以繁體中文將該 Study 的 candidate／baseline、base／stress、formal gates、targets、evidence validity、candidate freeze 狀態、限制與下一輪條件 append 至 `.study-developer/development-note/TSM.md`。
  - 通過對應 v003 validator／checker、必要測試、Ruff（若適用）與 `git diff --check`；結果與限制必須如實記錄，不以單筆交易或通過程式測試宣稱策略有效。
- **摘要**：承接既有 TSM 研究盤點，提出一個真正未嘗試過的量能先行、價格後確認的動能趨勢機制，完成可追溯的 v003 Development Study 與成果卡，讓後續是否值得凍結有明確證據可驗收。
- **進度／備註**：PM review 已驗收 `tsm-momentum-trend-volume-ramp--v001`。新假說為三個先前 session 內的短窗量能脈衝先於趨勢價格加速，與既有五日分散量能壓力及事件後固定突破區分。Trial evidence `valid`，candidate 11 筆／4 年、baseline 16 筆／5 年；candidate 與 baseline 的 formal Development gates 均有失敗，候選 freeze 在資格檢查前依法停止，`candidate_freeze: null`。成果卡已以 append-only 方式追加，並更正最終判定為 `failed`，同時保留 `targets: not_registered`、evidence validity 與限制。v003 `status`／`validate` 均 `completed`／`passed`，Development chain integrity 與 full semantic validation 通過，later stage `not_present`；target pytest 4 passed、Ruff passed、prepare synthetic runner、canonical YAML 與 `git diff --check` 均通過。未執行 Historical Evaluation、Terminal、challenge 或 replay。

### [TASK-003] 為 TSM 動能／趨勢 × 量先價行 Study 撰寫 Development 成果卡
- **狀態**：Done
- **優先級**：中
- **負責角色**：study 開發者
- **執行者**：Codex（study 開發者 subagent `01a0bc9b-7768-70f3-b92a-bf0cdda07f29`）
- **建立日期**：2026-09-20
- **更新日期**：2026-09-20
- **依賴／阻塞**：TASK-002 已完成；目標 Study 為 `tsm-momentum-trend-volume-lead--v001`
- **驗收條件**：
  - v003 Development 成果卡技能 checker exit 0，`development_evidence_validity=valid`。
  - 已逐 Trial 記錄 candidate／baseline 的 base、stress、formal gates、evidence validity、candidate freeze 狀態與限制，且以繁體中文 append 至既有 Development-only 成果卡集合；未覆寫或重排舊卡片。
  - 已通過 `git diff --check`；未讀取或修改禁止範圍，未執行 Evaluation、Terminal、runner、freeze 或 replay。
- **摘要**：完成 `tsm-momentum-trend-volume-lead--v001` 的 Development 成果卡，將正式 evidence 的結果與限制整理成人可讀的研究摘要，並明確區分 candidate／baseline、formal gates 與凍結資格。
- **進度／備註**：candidate base／stress 各 1 筆、1 年（2015），報酬 1.904%／1.622%，PF 均為 ∞，最大回撤均 0%；交易數、年度覆蓋與 stress leave-one-year-out 報酬 gates 失敗。baseline base／stress 各 16 筆、5 年，報酬 -0.573%／-2.793%，PF 0.956／0.780，最大回撤 4.548%／4.832%，多項 gates 失敗。成果卡狀態為 `failed`，Research targets 為 `not_registered`，`candidate_freeze_status` 為「尚不能判斷」；成果卡已寫入 `.study-developer/development-note/TSM.md`，由專案管理者驗收結案。

### [TASK-002] 在 v003 開發未嘗試的 TSM 動能／趨勢 × 量先價行假說
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Wegener（subagent `01a0ba99-df36-7172-bf24-5822bb887a96`）
- **建立日期**：2026-09-20
- **更新日期**：2026-09-20
- **依賴／阻塞**：無；v003 Workflow Release 已存在且為 Active
- **驗收條件**：
  - 已完成 TSM 既有假說盤點，並在 preregistration 固定新假說與其相對 v024 的機制差異。
  - 已依 v003 `development-to-freeze` 完成 prepare、create、唯一 Development trial、evidence validation，以及合法的 freeze-readiness／freeze 嘗試。
  - 已產出可驗證的 preregistration、candidate／baseline、implementation、runner、data bindings、Development evidence、事件鏈與 authority checkpoint；沒有執行 Historical Evaluation、Terminal、challenge 或 replay。
  - v003 status／validate、Subagent 回報的 4 項單元測試、Ruff 與 `git diff --check` 均通過；本次工作樹核對 `git diff --check` 亦通過。
- **摘要**：完成一個與既有 v024「單次放量事件＋事件後五日固定價突破」不同的新假說：上升趨勢中，先以五個已完成 session 的多日集中量能與上漲／持平日量能占比辨識量能壓力，再以當日均線趨勢、均線距離下限與至少 2% 一日價格加速確認動能延續。
- **進度／備註**：Development evidence 有效，但只產生 1 筆完成交易、1 個交易年度；`completed_trades`、`traded_years` 與 `minimum_stress_leave_one_year_out_return` 失敗。候選凍結未成功（`candidate_freeze: null`），流程依規則停止，沒有寫入 registry／provenance／candidate-frozen；這是有效的否證／不具凍結資格結果，不是漏做流程。Study：`tsm-momentum-trend-volume-lead--v001`。Event head：`ebb3c5eeb39b530dc4adae87125a9fd645543d812c2690c9c10d1a2d2a21e714`。主要 evidence：`research/tsm-momentum-trend-volume-lead--v001/`；事件鏈：`workflows/strategy-forward-replication-research--v003/studies/tsm-momentum-trend-volume-lead--v001/events/`。

### [TASK-001] 啟用 v003 並將 v002 標記為 Superseded
- **狀態**：Done
- **優先級**：高
- **負責角色**：workflow 執行者
- **執行者**：Chandrasekhar（subagent `01a0ba86-7d4e-7321-92e1-7efff6bd1078`）
- **建立日期**：2026-09-20
- **更新日期**：2026-09-20
- **依賴／阻塞**：無
- **驗收條件**：
  - v003 已確認 Release Candidate manifest、測試報告與 digest，並建立且通過有效的 `workflows/strategy-forward-replication-research--v003/release.yml` 驗證。
  - v002 原有 `release.yml`、Package、既有 Study、evidence 與 authority 仍保留，且原 Release Record 可獨立驗證。
  - `docs/workflow-lifecycle.md` 與 `workflows/README.md` 已更新目前狀態：v003 為 Active、v002 為 Superseded。
  - 沒有刪除或修改 v002 的不可變內容。
  - 沒有建立新 Study，也沒有執行 Historical Evaluation。
  - 完成 `git diff --check`。
- **摘要**：依 Release Candidate 證據重新計算 digest，由 Trusted Approver `ochowei` 建立 v003 Release Record，並更新 Workflow 治理狀態；v002 的 Package、Release Record、既有 Study、evidence 與 authority 均原地保留。
- **進度／備註**：workflow 執行者回報並由專案管理者驗收：v003 `release.yml` 的 `approved_at` 為實際 UTC `2026-09-19T16:38:39.747194Z`；manifest digest 為 `cf4a0918e76b49c508bddfb008ac8507db94b37878d024d121c336bceed3fee7`，test report digest 為 `2c960acaa8c9dbc8a5c9e88f4aebf74f5f7663a640d94c481594989235bd8157`，Workflow digest 為 `8b1425a9b418db86b6db2c162478b3cb9ff14042324ac185d7aaeddf019a5b95`。v003 與 v002 的 release validator 均通過，v002 無 diff，`git diff --check` 通過；未建立新 Study，未執行 Historical Evaluation。治理文件已更新為 v003 Active、v002 Superseded。
