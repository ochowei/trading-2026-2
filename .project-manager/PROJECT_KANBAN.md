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

### [TASK-007] 在 v003 開發下一個未嘗試的 TSM 動能趨勢 × 量先價行假說並撰寫成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Huygens（study 開發者 subagent `01a0be05-63cd-7660-8c85-b806dc8df4ea`）
- **建立日期**：2026-09-20
- **更新日期**：2026-09-20
- **依賴／阻塞**：無；v003 Workflow Release 已存在且為 Active
- **驗收條件**：
  - 先依允許範圍讀取 `.study-developer/development-note/TSM.md` 與既有 TSM Study，盤點已嘗試過的動能、趨勢及量先價行機制，提出一個有明確差異、不是改版本號／改名／無語義重發的全新假說。
  - 依 v003 `development-to-freeze` 流程建立新的 Development Study，固定 preregistration、candidate／baseline、implementation、runner、data bindings、明確派工與 provenance；完成唯一合法的 Development trial、evidence validation，以及規則允許的 freeze-readiness／freeze 嘗試。
  - 僅使用 v003 Development 範圍；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得覆寫、刪除或重排既有 Study、evidence、authority 或成果卡。
  - Development 完成後，依 v003 成果卡規範，以繁體中文 append-only 更新 `.study-developer/development-note/TSM.md`，如實記錄 candidate／baseline、base／stress、formal gates、research targets、evidence validity、candidate freeze 資格／狀態、provenance、限制與下一輪條件；缺少 evidence 時不得補猜數值。
  - 通過對應 v003 validator／checker、必要測試、Ruff（若適用）與 `git diff --check`；回報 Study ID、事件 head、修改檔案、驗證結果、實驗結果與任何實際缺件。
- **摘要**：根據 TSM Development 研究盤點，提出並驗證一個真正新的「量先於價、用於動能趨勢確認」機制，完成可追溯的 v003 Development Study 與成果卡，讓後續是否值得凍結有清楚且不越權的證據。
- **進度／備註**：由 Huygens 完成 Development 與 parent review 回修，已由 parent 驗收移至 Done。Study：`tsm-momentum-trend-volume-close-acceptance--v001`；唯一 Trial evidence `valid`，candidate 4 筆／4 年只失敗 `completed_trades`，baseline 16 筆／5 年且失敗多項核心與 stress gates；candidate freeze eligibility 不具資格，`candidate_freeze_status=尚不能判斷`。v003 `develop-to-freeze` 已完成 create、唯一 Development trial、evidence publish，並嘗試 freeze-readiness／freeze；事件 head：`1b578b648566674b169074f92388a56fa8c33980c8f501d47c68a02ffd5d1ace`，4 個事件，未產生 candidate-frozen。已 append-only 更新 `.study-developer/development-note/TSM.md`；`.venv/bin/python -m pytest -q` 4 passed、Ruff passed、v003 checker `eligible`／Development evidence `valid`／Historical Evaluation `not_inspected`、`git diff --check` passed。parent 另行重跑同一測試與 Ruff，均通過。公開規格核對確認 canonical tested rule 為 weighted close location `>=0.48`、位置差 `>=0.01`；immutable preregistration 文字中的 `0.65/0.10` 未被本 trial 執行，已在成果卡 append-only 明確揭露，不能以本結果代表該組門檻假說。明確未執行 Historical Evaluation、Terminal、challenge 或 replay；未覆寫、刪除或重排既有 Study、evidence、authority 或成果卡。建置技能所引用的路徑缺件已由實際 v003 workflow reference 補足，非阻塞。
- **Parent review 回修（2026-09-20）**：核對 `evidence/trials/.../{publication,inputs,candidate,baseline}.yml` 的 preregistration／engine／procedure bindings、`candidate-definition.yml`、`implementation-contract.yml` 與 runner／engine 後，canonical tested rule 明確是 `weighted close location >= 0.48`、加權減未加權位置差 `>= 0.01`；`0.65／0.10` 僅存在於 immutable preregistration 的已發布文字，未被本 Trial 執行，不得將結果表述為該組門檻假說。已在成果卡末尾 append-only 補上此明文更正；未改寫、刪除或重排 immutable preregistration、events、evidence、authority 或既有 Study。回修本身可供 parent 驗收，任務仍保留 Doing；不可修復的 immutable mismatch 已列為限制，若 parent 要求直接修正已發布 preregistration，需另作治理決策，不能在本回修內完成。實際缺件仍為 candidate freeze／provenance 凍結事件，且 candidate 4<20 formal gate 失敗；未新增 Study、trial 或研究結果。
- **回修驗證結果**：v003 checker `status=eligible`、`development_evidence_validity=valid`、`candidate_freeze_status=尚不能判斷`；既有 `status`／`validate` 均通過，chain integrity／full semantic validation 為 true，事件 head 維持 `1b578b648566674b169074f92388a56fa8c33980c8f501d47c68a02ffd5d1ace`；單元測試 4 passed、Ruff passed、`git diff --check` passed。沒有執行或觸碰 Historical Evaluation、Terminal、challenge、replay，也沒有重跑 Development。
---

## ⏳ Pending

> 因阻塞、依賴或等待決策而暫停的任務。

（目前沒有 Pending 任務）

---

## ✅ Done

> 已完成工作並由專案管理者驗收確認的任務。

### [TASK-006] 在 v003 開發下一個未嘗試的 TSM 動能趨勢 × 量先價行假說並撰寫成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Parfit（study 開發者 subagent `01a0bde5-7c75-7253-8faa-fb1b167132f9`）
- **建立日期**：2026-09-20
- **更新日期**：2026-09-20
- **依賴／阻塞**：無；v003 Workflow Release 已存在且為 Active
- **驗收條件**：
  - 先依允許範圍讀取 `.study-developer/development-note/TSM.md` 與既有 TSM Study，整理已嘗試過的動能、趨勢及量先價行機制；提出一個可追溯、確實未嘗試過的新假說，不得只是改版本號、改名稱或做無語義差異的重發。
  - 依 v003 `development-to-freeze` 流程建立新的 Development Study，固定 preregistration、candidate／baseline、implementation、runner、data bindings、明確派工與 provenance；完成唯一合法的 Development trial、evidence validation，以及規則允許的 freeze-readiness／freeze 嘗試。
  - 僅使用 v003 Development 範圍；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得覆寫、刪除或重排既有 Study、evidence、authority 或成果卡。
  - Development 完成後，依 v003 成果卡規範，以繁體中文 append-only 更新 `.study-developer/development-note/TSM.md`，如實記錄 candidate／baseline、base／stress、formal gates、research targets、evidence validity、candidate freeze 資格／狀態、provenance、限制與下一輪條件；缺少 evidence 時不得補猜數值。
  - 通過對應 v003 validator／checker、必要測試、Ruff（若適用）與 `git diff --check`；回報 Study ID、事件 head、修改檔案、驗證結果、實驗結果與任何實際缺件。
- **摘要**：根據既有 TSM Development 研究盤點，提出一個真正新的「量先於價、用於動能趨勢確認」機制，完成可追溯的 v003 Development Study 與成果卡，讓後續是否值得凍結有清楚且不越權的證據。
- **進度／備註**：Study `tsm-momentum-trend-volume-efficiency--v001` 已完成唯一 v003 Development trial。新機制為訊號日前五個完成 session 的成交量加權日內高低價活動／未加權活動比率至少 1.15，再由當日趨勢與價格加速確認；與既有五日量能壓力、三日量能脈衝、量價吸收及 v024 固定突破不同。事件 head：`0d4d114e3a6d303c8bdb66d2aa6de03e5eb7330cdcb6371af963522a841d0ad4`。Candidate evidence `valid`：base 6 筆、5.208% 報酬、PF 3.427；stress 6 筆、3.930% 報酬、PF 2.853；只因 `completed_trades` 低於 20 筆而 formal gate 失敗，`candidate_freeze: null`，freeze-readiness／freeze 未完成。Baseline：base 16 筆、-0.573%／PF 0.956；stress 16 筆、-2.793%／PF 0.780。成果卡已依 v003 規範以繁體中文 append-only 寫入，checker 通過。v003 prepare、create、development、status／validate 回報通過；parent 重新執行目標 pytest 得到 4 passed、Ruff passed、`git diff --check` passed。未執行 Historical Evaluation、Terminal、challenge 或 replay；parent review 通過，移至 Done。

### [TASK-005] 在 v003 發想並開發未嘗試的 TSM 動能趨勢 × 量先價行假說，完成成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Aquinas（study 開發者 subagent `01a0bcfb-1b30-76a2-b130-2f331b03b879`）
- **建立日期**：2026-09-20
- **更新日期**：2026-09-20
- **依賴／阻塞**：無；v003 Workflow Release 已存在且為 Active
- **驗收條件**：
  - 先讀取 `.study-developer/development-note/TSM.md` 及允許範圍內的既有 TSM Study，整理已嘗試過的動能、趨勢與量先價行機制，提出一個可追溯且不是既有規則改版本號或小幅重命名的全新假說。
  - 依 v003 `development-to-freeze` 流程建立新的 Development Study，固定 preregistration、candidate／baseline、implementation、runner、data bindings、明確派工與 provenance；完成唯一合法的 Development trial、evidence validation，以及規則允許的 freeze-readiness／freeze 嘗試。
  - Development 只使用 v003 的 Development 範圍；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得覆寫、刪除或重排既有 Study、evidence、authority 或成果卡。
  - Development 完成後，依 v003 成果卡規範，將該 Study 的 candidate／baseline、base／stress、formal gates、research targets、evidence validity、candidate freeze 資格／狀態、provenance、限制與下一輪條件，以繁體中文 append 至 `.study-developer/development-note/TSM.md`；若 evidence 不完整，必須如實標示不可用或尚不能判斷，不得補猜數值。
  - 通過對應 v003 validator／checker、必要測試、Ruff（若適用）與 `git diff --check`；不得以程式存在、測試通過或單筆交易宣稱策略有效。回報 Study ID、事件 head、修改檔案、驗證結果與任何實際缺件。
- **摘要**：根據 `TSM.md` 的既有研究盤點，在 v003 workflow 中發想一個尚未嘗試的「量先於價、用於動能趨勢確認」機制，完成可追溯的 Development Study 與成果卡，讓後續是否值得凍結有清楚且不越權的證據。
- **進度／備註**：使用者派工原文：「讓 study 開發者根據[TSM.md](.study-developer/development-note/TSM.md) 在 v003 的 workflow 發想一個沒有嘗試過的動能趨勢跟量先價行的假說，並進行開發，開發完成後為這個 study 撰寫成果卡。」由 `codex-study-developer-task-005` 完成 Development。Study：`tsm-momentum-trend-volume-absorption--v001`；新機制是訊號日前五個 session 內至少一個「成交量≥此前20日均量1.20倍且收盤絕對變化≤0.5%」的量價吸收，之後才以當日≥2% 價格加速確認；與既有 `volume-lead` 五日分散量能壓力、`volume-ramp` 三日單次脈衝及 v024 事件後固定價突破有明確差異。事件 head：`a3763b5f576aced2987d1dd5dd549111b927a007cd6a65cbb9b2996441413b32`；v003 `status`／`validate`：completed／passed，chain integrity 與 full semantic validation 通過，later stage `not_present`。Development evidence：`valid`；candidate 5 筆／3 年，base 報酬 3.9698%／PF 2.9487／回撤 1.9991%，stress 報酬 2.9420%／PF 2.4477／回撤 1.9997%；candidate formal gates 失敗於交易數、stress bootstrap 正報酬比、stress leave-one-year-out PF／報酬，`candidate_freeze: null`，freeze-readiness 與 freeze 均以 `qualification-failed` 依法停止。baseline 16 筆／5 年，base -0.5729%／PF 0.9556／回撤 4.5483%，stress -2.7935%／PF 0.7800／回撤 4.8322%，多項 gates 失敗。成果卡已 append 至 `.study-developer/development-note/TSM.md`，判定 `failed`、targets `not_registered`、candidate freeze status「尚不能判斷」。依 `.study-developer/AGENTS.md` 的角色限制，PM 未直接開啟成果卡；以 worker 回報的成果卡 checker `eligible`、公開 Study／evidence／事件鏈及下列驗證結果完成 review。驗證命令／結果：v003 `prepare` passed；v003 `create`、`development` completed；v003 `status`／`validate` passed；evidence validity `valid`；PM 重新執行目標 pytest 得到 4 passed、Ruff check passed；worker 回報 `git diff --check` passed。未執行 Historical Evaluation、Terminal、challenge、replay。PM review：通過，移至 Done。
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
