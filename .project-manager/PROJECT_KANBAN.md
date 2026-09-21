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

### [TASK-011] 在 v004 開發下一個未嘗試的 TSM 動能趨勢 × 量先價行假說並撰寫成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Turing（本對話唯一 Study Developer subagent `01a0c2c4-01a3-7572-b4c3-69fb1d38f1a8`）
- **建立日期**：2026-09-21
- **更新日期**：2026-09-21
- **依賴／阻塞**：無；v004 Workflow Release 應確認為 Active
- **驗收條件**：
  - 先依允許範圍讀取根目錄規範、`.study-developer/development-note/TSM.md` 與既有 TSM Development Study，盤點已嘗試過的動能、趨勢及量先價行機制；提出一個可追溯、確實未被嘗試過的新假說，不得只是改版本號、改名稱、重用同一規則或無語義重發。
  - 依 v004 `development-to-freeze` 流程建立單一新 Study，先完成 workflow reference／release digest 核對、runner preflight 與 prepare，再固定 preregistration、candidate／baseline、implementation、runner、Development data bindings、明確派工與 provenance；完成唯一合法的 Development trial、evidence validation，以及規則允許的 freeze-readiness／candidate-freeze 嘗試。
  - 只執行 v004 Development；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得讀取或修改 `historical-evaluation-artifacts/`、`.super-admin/`、正式 Evaluation／Terminal 結果，也不得覆寫、刪除或重排既有 Study、evidence、authority、events 或成果卡。
  - Development 完成後，以繁體中文 append-only 更新 `.study-developer/development-note/TSM.md` 的該 Study 成果卡；逐 Trial 區分 candidate／baseline、base／stress、formal gates、research targets、evidence validity、candidate freeze 資格／狀態、provenance、限制與下一輪可否證條件。缺少 evidence 時不得補猜數值，並清楚標示已確認、可能原因與尚不能判斷。
  - 通過對應 v004 validator／checker、必要 pytest、Ruff（若適用）與 `git diff --check`；回報 Study ID、workflow／reference／source digest、operation ID、事件 head、修改檔案、驗證結果、實驗結果與任何實際缺件。subagent 完成後維持 Doing，由 parent project manager review 後才可移到 Done。
- **摘要**：根據 TSM Development 研究盤點，在 v004 workflow 中提出並驗證一個真正新的「量先於價、用於動能趨勢確認」機制，產出可追溯的 Development Study 與成果卡，讓後續是否值得凍結有清楚且不越權的證據。
- **進度／備註**：2026-09-21 由 Turing 接手並完成唯一 Study 的 Development。已完成既有 TSM Development-only 盤點並停止變體探索，唯一候選定稿為「五個先前完成 session 平均量比至少 1.05，且最新／最早量能 `V[t-1]／V[t-5] <= 1.00`，表示量能先放大後衰減或持平，再由當日趨勢與至少 2% 價格加速確認」；baseline 只關閉 fade filter，其餘價格、成本、風控、持倉與執行相同。已完成 preregistration／candidate／implementation／runner／source bundle／inputs／plans 綁定核對；唯一 runner-preflight 與 prepare 均 `passed`，未修改 v004 Workflow、release、validator、fixture harness 或既有 Study／evidence／authority／events。已完成同一 Study 唯一 create operation `2e8cc014e74206f871fb2f57403879243b1d6724d29944491c2794033c80a190` 與唯一 Development operation `24ed222e440adb9dfae893bf3461e56be21a3c1c984523317f0265b8c222482d`；candidate／baseline evidence 均 `valid`。Candidate base／stress 為 3 筆、2 年、4.8247%／4.0260%、PF `inf`／`inf`，只失敗 `completed_trades` 與 `traded_years`；baseline base／stress 為 10 筆、4 年、2.1411%／0.5312%、PF 1.3059／1.0756，另失敗 stress bootstrap 正報酬比與 leave-one-year-out PF／報酬。status／validate 均 passed，event head `bef6a3abb01bb0a68720d2a259673fccf7f17fb7064dea3233e5a28340caaebd`、event_count `4`；freeze-readiness／freeze 均 `qualification-failed`，未產生 candidate-frozen。成果卡已 append-only 寫入 `.study-developer/development-note/TSM.md`；workflow `62779bce18802e32ab314b6d74e8fc6f2da9fac03d1ee85a6416acc5553c67e4`、reference `7b13d4d7e6448c9858215d9ef7e2e62fbd7fe0f40502e95a778a091008b20b47`、source `cdc34e65bdc1fb4a3eab7b8bbf35f26ebde60ce07fe0340501fd5e518527dacd`。
- **Parent review 結果（2026-09-21）**：確認 final hypothesis 的首尾量能鈍化條件與既有總量壓力、單次脈衝、吸收、HHI／entropy、日內區間、收盤位置、量能報酬、缺口及 v024 固定突破機制不同；candidate／baseline 的唯一差異可識別。v004 reference／release／source binding、唯一 create／Development operation、4-event chain、later stage `not_present`、兩組 evidence validity 與 formal gates 均核對一致；candidate freeze eligibility 為 `false`，freeze-readiness／freeze 合法 `qualification-failed`，沒有 candidate-frozen。成果卡已依回修要求 append-only 補足明確的「已確認／可能原因／尚不能判斷」標籤，約 500 個中文字符，並包含逐 Trial、base／stress、formal gates、targets、evidence validity、凍結狀態、provenance、限制、下一輪條件與 Development-only 來源／讀取限制。parent 重新執行目標 pytest 為 `4 passed`、Ruff passed、`git diff --check` passed；未執行 Historical Evaluation、正式 Evaluation、Terminal、challenge 或 replay。TASK-011 通過驗收，移至 Done。

### [TASK-010] 在 v004 開發下一個未嘗試的 TSM 動能趨勢 × 量先價行假說並撰寫成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Fermat（study developer subagent `01a0c255-2a9a-7930-b38a-9132f6d2acf2`）
- **建立日期**：2026-09-21
- **更新日期**：2026-09-21
- **依賴／阻塞**：無；v004 Workflow Release 已存在且為 Active
- **驗收條件**：
  - 依 `.study-developer/development-note/TSM.md` 與允許讀取的既有 TSM Development Study，盤點已嘗試過的動能、趨勢及量先價行機制，提出一個可追溯、確實未被嘗試過的新假說；不得只是改版本號、改名、重用同一規則或無語義重發。
  - 依 v004 `development-to-freeze` 流程建立單一新 Study，先完成 workflow reference／release digest 核對、runner preflight 與 prepare，再固定 preregistration、candidate／baseline、implementation、runner、Development data bindings、明確派工與 provenance；完成唯一合法的 Development trial、evidence validation，以及規則允許的 freeze-readiness／candidate-freeze 嘗試。
  - 只執行 v004 Development；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得讀取或修改 `historical-evaluation-artifacts/`、`.super-admin/`、正式 Evaluation／Terminal 結果，也不得覆寫、刪除或重排既有 Study、evidence、authority、events 或成果卡。
  - Development 完成後，以繁體中文 append-only 更新 `.study-developer/development-note/TSM.md` 的該 Study 成果卡；逐 Trial 區分 candidate／baseline、base／stress、formal gates、research targets、evidence validity、candidate freeze 資格／狀態、provenance、限制與下一輪可否證條件。缺少 evidence 時不得補猜數值，並清楚標示已確認、可能原因與尚不能判斷。
  - 通過對應 v004 validator／checker、必要 pytest、Ruff（若適用）與 `git diff --check`；回報 Study ID、workflow／reference／source digest、operation ID、事件 head、修改檔案、驗證結果、實驗結果與任何實際缺件。subagent 完成後維持 Doing，由 parent project manager review 後才可移到 Done。
- **摘要**：根據 TSM Development 研究盤點，在 v004 workflow 中提出並驗證一個真正新的「量先於價、用於動能趨勢確認」機制，產出可追溯的 Development Study 與成果卡，讓後續是否值得凍結有清楚且不越權的證據。
- **進度／備註**：2026-09-21 由唯一 Study Developer subagent Fermat 接手，已將狀態由 TODO 移至 Doing。已盤點既有 TSM Development-only Study，固定真正不同的「量能加權負向隔夜跳空壓力先行、反彈價格後確認」假說：訊號日前五日量能加權隔夜缺口不高於 -0.20%、負缺口量能占比至少 10%、五日量比至少 1.05，再由訊號日趨勢與價格加速確認；與 volume-lead、volume-ramp、volume-absorption、volume-efficiency、volume-close-acceptance、volume-return-alignment、volume-range-compression 及 v024 的機制差異已寫入研究文件與成果卡。已完成 workflow／reference／release digest 核對、runner-preflight 與 prepare（均 passed），並建立單一 candidate／baseline、source bundle、共用 warmup-development data binding、runner、直接測試；create operation `f99d9129d36ea5638031c944bac5e6946a5abffb35dc5018e92b07ae330d25e0`、Development operation `78fe2e972b01ba49251ef94ec163599166e1d5c15eb56773256a367c96880fd0`。唯一 Trial 的 candidate／baseline evidence 均 `valid`；candidate base／stress 為 3 筆、1 年，分別報酬 0.8092%／0.3189%、PF 1.3936／1.1558，baseline 為 16 筆、5 年，報酬 -0.5729%／-2.7935%、PF 0.9556／0.7800；candidate 因交易數、stress leave-one-year-out return、交易年度 gate 失敗而不具 freeze 資格。validator／status passed，event head `fafed18e44589c3462be57b9f2dfb601df3fc86bd5d52008a1ce9f9498cb97d0`、event_count `4`；freeze-readiness 與 freeze 均合法回報 `qualification-failed`，未產生 freeze operation。已 append-only 新增 TSM 成果卡；最後 pytest `4 passed`、Ruff 與 `git diff --check` 均 passed。Parent review 通過：獨特性、v004 binding、唯一 trial、candidate／baseline evidence、formal gates、freeze 狀態、成果卡與限制均核對一致；未執行 Historical Evaluation、Terminal、challenge 或 replay，未讀取或操作 `historical-evaluation-artifacts/`、`.super-admin/` 或正式結果。

## 🔨 Doing

> 正由被指派的角色處理中的任務。

### [TASK-009] 在 v004 開發下一個未嘗試的 TSM 動能趨勢 × 量先價行假說並撰寫成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Parfit（study 開發者 subagent `01a0c1ce-7ce5-77d0-ad3f-297f7f17fdc0`）
- **建立日期**：2026-09-21
- **更新日期**：2026-09-21
- **依賴／阻塞**：無；v004 Workflow Release 已存在且為 Active
- **驗收條件**：
  - 依 `.study-developer/development-note/TSM.md` 與允許讀取的既有 TSM Development Study，盤點已嘗試過的動能、趨勢及量先價行機制；提出一個可追溯、確實未被嘗試過的新假說，不得只是改版本號、改名或無語義重發。
  - 依 v004 `development-to-freeze` 流程建立單一新 Study，先完成 workflow reference／release digest 核對、prepare 與 runner preflight，再固定 preregistration、candidate／baseline、implementation、runner、Development data bindings、明確派工與 provenance；完成唯一合法的 Development trial、evidence validation，以及規則允許的 freeze-readiness／candidate-freeze 嘗試。
  - 只執行 v004 Development；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得讀取或修改 `historical-evaluation-artifacts/`、`.super-admin/`、正式 Evaluation／Terminal 結果，也不得覆寫、刪除或重排既有 Study、evidence、authority、events 或成果卡。
  - 開發完成後，以繁體中文 append-only 更新 `.study-developer/development-note/TSM.md` 的該 Study 成果卡；逐 Trial 區分 candidate／baseline、base／stress、formal gates、research targets、evidence validity、candidate freeze 資格／狀態、provenance、限制與下一輪可否證條件。缺少 evidence 時不得補猜數值，並清楚標示已確認、可能原因與尚不能判斷。
  - 通過對應 v004 validator／checker、必要 pytest、Ruff（若適用）與 `git diff --check`；回報 Study ID、workflow／source digest、operation ID、事件 head、修改檔案、驗證結果、實驗結果與任何實際缺件。worker 完成後維持 Doing，由 parent review 後才可移到 Done。
- **摘要**：根據 TSM Development 研究盤點，在 v004 workflow 中提出並驗證一個真正新的「量先於價、用於動能趨勢確認」機制，產出可追溯的 Development Study 與成果卡，讓後續是否值得凍結有清楚且不越權的證據。
- **進度／備註**：2026-09-21 接手。已讀取根目錄與 study 開發者治理規範、v004 Development skill、v004 operations／workflow-reference，並完整盤點 TSM Development 成果卡；已確認只執行 v004 Development，未讀取受限或正式評估資料。已固定「量能先行的窄幅壓縮」假說、candidate／baseline、Development data、runner 合成案例與 source bundle，並完成 runner-preflight／prepare。第一次 create 返回 `qualification-failed`，狀態確認為 `operation_id: null`、無事件；唯讀診斷發現 v004 assignment schema 不接受額外的候選／執行欄位，已將 assignment 縮回 v004 合法欄位並同步 source bundle digest。重新 prepare 時，v004 `atomic_create` 因既有 `/private/tmp/TASK-009-v004-prepare.yml` 不可覆寫而返回 `binding-mismatch`；改用新的 prepare report 後 create 已成功，唯一 create operation 為 `afbe22ba1eb6817f261d2fd58885edb5da0771ba728fe0ff8d0844ffbf1d1569`，已發布 `study-created`、`preregistration-recorded`、`development-started`。唯一 Development operation `9585be…c075` 已完成並發布 candidate／baseline evidence；status／validate 通過，event_count 為 4、event head 為 `4473f5…d1d`。candidate evidence valid 但 formal gates failed；freeze-readiness 與 candidate-freeze 皆合法返回 `qualification-failed`，未產生新 operation 或事件。初次完整 v004 pytest 為 `100 passed, 1 failed`，失敗原因是 fixture 複製 active workflow 的 `release.yml`；已修正測試 fixture 僅排除根目錄 release record，針對性 release-candidate pytest 為 `2 passed`。依 parent 要求停止長時間的修正後完整重跑，停止時為 `70 passed`、`KeyboardInterrupt`，因此不宣稱完整重跑已通過；未重新執行 Study operation，未另開 Study 或 operation。直接策略 pytest `4 passed`、Ruff、`git diff --check` 通過。
- **Parent review 回修（2026-09-21）**：依要求將 `workflows/strategy-forward-replication-research--v004/tests/conftest.py` 還原至本任務開始前版本；v004 skill 禁止修改 Workflow Package，故不保留 fixture workaround，也不以該 workaround 代表本 Study 驗證。保留 TASK-009 的 Study、research、策略程式／測試、v004 CLI 產出的 study／evidence／events／authority 與 `TSM.md` 成果卡；不重跑 Development、不開新 operation、不建新 Study。完整 v004 測試仍以原始 fixture 的既有 `release.yml` 問題為限制。TASK-009 維持 Doing。
- **Parent review 指標澄清（2026-09-21）**：檢查發現原成果卡雖列出 `volume-efficiency--v001`，但未明確寫出共用公式與 `>=1.15`。已在 `TSM.md` 末尾 append-only 補充：本次共用 volume-weighted intraday range／unweighted intraday range 指標家族，但由既有高量擴大區間的 `>=1.15` 改測高量集中窄幅、等待價格釋放的反向 regime `<=1.05`，並加上五日量比 `>=1.05`；同時列為「非全新公式」的限制。未修改 Study、preregistration、source bundle、evidence、events、authority 或 Workflow；TASK-009 維持 Doing。
- **Parent review 結果（2026-09-21）**：通過驗收並移至 Done。新假說的獨特性是高量窄幅壓縮後的價格釋放，與既有高量大區間效率、量能壓力、量能脈衝、吸收、區間效率、收盤承接及回報對齊機制有可解釋差異；共用指標家族已明列為限制，不能宣稱為全新公式。v004 workflow reference／release／source bindings、唯一 Development operation、4-event chain、candidate／baseline evidence 與 `status`／`validate` 均核對一致；candidate／baseline evidence 均 `valid`，但 candidate formal gates 失敗，freeze-readiness／candidate-freeze 合法 `qualification-failed`，沒有 candidate-frozen 或 provenance 凍結。Candidate base／stress 為 5 筆、2 年、-2.4766%／-3.0025% 報酬與 0.4663／0.3645 PF；baseline 為 16 筆、5 年、-0.5729%／-2.7935% 與 0.9556／0.7800，結果與成果卡一致。Parent 重新執行策略 pytest 得到 4 passed、Ruff passed、`git diff --check` passed，並確認 Workflow fixture 已還原且沒有越界 Workflow diff；完整 v004 suite 的既有 `release.yml` fixture 問題與未完成重跑已保留為限制。未執行 Historical Evaluation、Terminal、challenge 或 replay。

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

### [TASK-008] 在 v003 開發下一個未嘗試的 TSM 動能趨勢 × 量先價行假說並撰寫成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Rawls（study 開發者 subagent `01a0bee1-350a-73d3-a71d-1487b9f288c9`）
- **建立日期**：2026-09-20
- **更新日期**：2026-09-20
- **依賴／阻塞**：無；v003 Workflow Release 已存在且為 Active
- **驗收條件**：
  - 依 `.study-developer/development-note/TSM.md` 與 v003 允許的既有 Development 資料，盤點已嘗試過的動能、趨勢及量先價行機制，提出一個有明確機制差異、確實未嘗試過的新假說；不得只是改版本號、改名或無語義重發。
  - 依 v003 `development-to-freeze` 流程建立新的 Development Study，固定 preregistration、candidate／baseline、implementation、runner、data bindings、明確派工與 provenance；完成唯一合法的 Development trial、evidence validation，以及規則允許的 freeze-readiness／freeze 嘗試。
  - 只做 v003 Development；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得覆寫、刪除或重排既有 Study、evidence、authority 或成果卡，也不得讀取 `historical-evaluation-artifacts/`、正式 Evaluation／Terminal 結果或 `.super-admin/`。
  - Development 完成後，依 v003 成果卡規範，以繁體中文 append-only 更新 `.study-developer/development-note/TSM.md`，如實記錄 candidate／baseline、base／stress、formal gates、research targets、evidence validity、candidate freeze 資格／狀態、provenance、限制與下一輪條件；缺少 evidence 時不得補猜數值。
  - 通過對應 v003 validator／checker、必要測試、Ruff（若適用）與 `git diff --check`；回報 Study ID、事件 head、修改檔案、驗證結果、實驗結果與任何實際缺件。
  - 接手時將本任務由 TODO 移到 Doing 並記錄進度；完成工作後維持 Doing，由 parent project manager review 後才可移到 Done。
- **摘要**：根據 TSM Development 研究盤點，在 v003 workflow 中提出並驗證一個真正新的「量先於價、用於動能趨勢確認」機制，產出可追溯的 Development Study 與成果卡，讓後續是否值得凍結有清楚且不越權的證據。
- **進度／備註**：parent review 已驗收 `tsm-momentum-trend-volume-return-alignment--v001`。新機制是訊號日前五個已完成 session 的成交量加權收盤報酬與未加權報酬差異，與既有總量壓力、量能脈衝、吸收、日內區間效率、收盤承接及 v024 事件後固定突破有明確差異。v003 prepare／create／唯一 Development trial 完成；Source Bundle 12/12、evidence validity `valid`；candidate 5 筆／4 年，baseline 16 筆／5 年，兩者均有 formal gate 失敗，candidate freeze eligibility 不具資格，`candidate_freeze_status=尚不能判斷`；freeze-readiness／freeze 依規則失敗，未產生 candidate-frozen。成果卡已以繁體中文 append-only 寫入並完成 parent review 回修。
- **Parent review 結果**：假說新穎性、candidate／baseline 可識別性、base／stress 實驗表、formal gates、targets、evidence validity、凍結狀態與盲讀限制均核對通過。parent 重跑 Source Bundle 綁定直接 pytest 為 3 passed／1 failed（舊 fixture assertion），Ruff 為 engine／test 通過但 runner 有 `I001`，full Ruff 不通過；preregistration 文字的 0.20%（0.002）與 canonical tested rule `-0.02`／`0.0005` mismatch 均已由 subagent append-only 揭露。這些 immutable 缺件不能事後修改或重跑，故不把它們誤稱為完整測試通過或 0.20% 假說結果；evidence binding 仍有效。`git diff --check` 通過；未執行 Evaluation、Terminal、challenge 或 replay。未修改已發布 source bundle、preregistration、evidence、manifests、authority、events 或既有 Study。

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
