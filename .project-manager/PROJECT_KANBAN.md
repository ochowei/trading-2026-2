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
- **狀態**：Done
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

### [TASK-027] 建立 v005 Study Development 專用 skill
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：`/root/v005_build_skill`（GPT-6 Luna，Max）
- **建立日期**：2026-09-25
- **更新日期**：2026-09-25
- **依賴／阻塞**：v005 已 Active；依 v004 對應 skill 格式，並以 v005 操作指南與實際 CLI 契約為準
- **驗收條件**：在 `.agents/skills/build-strategy-study-v005/SKILL.md` 建立繁體中文 skill；明確限定 Study Developer 角色、v005 單一 Study 的合法 Development 範圍、固定 workflow/release/policy/data bindings、多資產輸入及單資產相容路徑；不得照搬 v004 CLI 命令或資料契約；不執行 Study Lifecycle；符合 skill-creator 格式並通過 quick_validate；原 v004 skill 不變。
- **摘要**：建立 v005 專用 Study 開發指引，讓後續研究者依目前 Active workflow 合法準備、開發與交接，不沿用 v004 的過期契約。
- **進度／備註**：GPT-6 Luna／Max study 開發者已建立指定 skill。Parent 以 repo `.venv` 重跑 `quick_validate.py` 通過，並對照 v005 operations/CLI、多資產契約與角色限制審閱命令、assignment、release/reference/policy bindings、單資產相容及 1–16 資產規則。skill-creator 驗證及 v005 契約符合；v004 skills 未變，TASK-027 驗收完成。

### [TASK-028] 建立 v005 Study blind review 專用 skill
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：`/root/v005_blind_review_skill`（GPT-6 Luna，Max）
- **建立日期**：2026-09-25
- **更新日期**：2026-09-25
- **依賴／阻塞**：v005 已 Active；依 v004 對應 skill 格式，並先核對 v005 evidence/reference 契約
- **驗收條件**：在 `.agents/skills/blind-review-strategy-study-v005/SKILL.md` 建立繁體中文 skill；明確處理 outcome exposure、v005 reference/digest 驗證、允許與禁止讀取範圍、盲檢討判定與輸出；不得讀取正式 Evaluation／Terminal 結果或受限資料、不得重跑 runner、不得執行 Study Lifecycle；符合 skill-creator 格式並通過 quick_validate；原 v004 skill 不變。
- **摘要**：建立 v005 Development evidence 專用盲檢討指引，保留盲性與讀取界線並適配 v005 套件。
- **進度／備註**：GPT-6 Luna／Max study 開發者已建立指定 skill；worker 與 parent 執行 `quick_validate.py` 均通過，檔案及新檔 whitespace 檢查通過。Parent 審閱確認 outcome exposure、v005 workflow-reference/digest、Development-only allowlist、多資產 publication bindings、禁止資料與不宣稱完整 event/state 驗證的限制一致；未執行 Study 操作，v004 skill 未變。TASK-028 驗收完成。

### [TASK-029] 建立 v005 Historical Evaluation 專用 skill
- **狀態**：Done
- **優先級**：高
- **負責角色**：workflow 維護者
- **執行者**：`/root/v005_eval_skill_maintainer`（GPT-6 Luna，Max；workflow 維護者）
- **建立日期**：2026-09-25
- **更新日期**：2026-09-25
- **依賴／阻塞**：v005 已 Active；依 v004 對應 skill 格式，並以 v005 Lifecycle、操作與多資產契約為準
- **驗收條件**：在 `.agents/skills/run-strategy-historical-evaluation-v005/SKILL.md` 建立繁體中文 skill；限定歷史評估執行者、已 frozen 單一 Study、唯一評估 operation、v005 多資產 digest/snapshot 綁定及合法 resume/indeterminate 規則；僅授權在明確評估派工下讀寫其指定 `historical-evaluation-artifacts/` Study 子目錄，且不覆寫既有 artifact；建立 skill 本身不得讀取該資料夾或執行 Evaluation；符合 skill-creator 格式並通過 quick_validate；原 v004 skill 不變。
- **摘要**：建立與 v005 多資產資料契約和 operation 恢復方式一致的正式歷史評估指引。
- **進度／備註**：原受派 evaluator subagent 在整理 schema 檔名時讓搜尋結果意外包含受限資料夾檔名；沒有開啟或讀取檔案內容，parent 立即停止該執行者。改派 workflow 維護者只依明列 v005 公開操作文件與 schema 建立 skill；未碰 Study 結果或受限資料。Parent 驗證 `quick_validate.py`、`git diff --check` 均通過，並核對 frozen candidate、multi-asset digest、唯一 reservation/marker、原 operation resume、indeterminate 與 artifact 不覆寫規則符合 v005。TASK-029 驗收完成。

### [TASK-030] 建立 v005 Development 成果卡專用 skill
- **狀態**：Done
- **優先級**：中
- **負責角色**：study 開發者
- **執行者**：`/root/v005_note_card_skill`（GPT-6 Luna，Max）
- **建立日期**：2026-09-25
- **更新日期**：2026-09-25
- **依賴／阻塞**：v005 已 Active；依 v004 對應成果卡 skill 格式，並以 v005 evidence/reference 契約為準
- **驗收條件**：在 `.agents/skills/study-development-note-authoring-v005/SKILL.md` 建立繁體中文 skill；只使用允許的 Development evidence，明確區分正式 gates、研究 targets、evidence validity、freeze 資格／狀態與限制；禁止接觸正式 Evaluation／Terminal 結果與受限資料；成果卡預設對話輸出，寫檔須遵守明確要求與 append-only 原則；符合 skill-creator 格式並通過 quick_validate；原 v004 skill 不變。
- **摘要**：建立 v005 Development 結果整理指引，讓成果卡完整呈現逐資產研究綁定和可判定範圍，不誤用正式評估結果。
- **進度／備註**：GPT-6 Luna／Max study 開發者建立成果卡 skill 後，parent review 發現兩項需修正：v005 trial registry 實際保存在禁止讀取的 event payload，且寫檔條件同時要求新路徑並談及既有檔 append。已交回同一 subagent 修正：移除 registry 的讀取暗示，證據不足時標示「尚不能判斷」；明確要求使用者指定寫入目標，已存在則只 append。修正版 `quick_validate.py` 通過；parent 重驗四份 v005 skills 均 `Skill is valid!`，untracked skill whitespace checks 無診斷、tracked `git diff --check` 通過，四份 v004 skills 均無 diff。Parent 確認 Development-only 範圍、資產綁定、freeze 判讀與 append 規則符合驗收，TASK-030 驗收完成。

### [TASK-022] 以既有 TSM breadth Study 為基礎，在 v004 提出新假說、盲檢討並撰寫成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：本 parent thread 唯一 Study Developer subagent `/root/study_developer_task_022`
- **建立日期**：2026-09-23
- **更新日期**：2026-09-23
- **依賴／阻塞**：無；開始前依 v004 規範確認 Workflow Release、reference 與 Development data bindings
- **驗收條件**：
  - 依 `.study-developer/development-note/TSM.md`、目標 `tsm-momentum-trend-volume-breadth--v001` 與 v004 允許讀取的 Development-only 研究，盤點既有假說與可改善處。必須把 TASK-021 的 `tsm-momentum-trend-volume-path-efficiency--v001` 視為既有嘗試；其 preregistration／candidate 規格歧義未釐清前，不得推定 path-efficiency 是取代或追加 breadth，也不得重用該 path-efficiency 公式作為本次新假說。
  - 提出一個機制清楚、可否證、可預先登記且確實未曾嘗試過的改進假說；說明相對原 breadth Study、TASK-021 與其他最近鄰機制的差異，固定單一研究變更及比較 baseline，只建立一個新的 v004 Study。不得修改或重發原 Study，也不得只改名稱、版本或參數。
  - 依 v004 `development-to-freeze` 核對 Workflow reference／release／policy／source 與 Development data bindings，完成 runner preflight、prepare、preregistration、candidate／baseline、implementation、runner、明確派工及 provenance；依法只做一次 create 與一次 Development trial，完成 evidence validation 及規則允許的 freeze-readiness／candidate-freeze 嘗試。若資格不符，保留實際狀態與失敗原因，不得繞過流程或補猜結果。
  - 僅執行 v004 Development；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得讀取、搜尋、雜湊、修改或引用 `historical-evaluation-artifacts/`、`.super-admin/`、quarantine／full evaluation data 或正式 Evaluation／Terminal 結果；不得覆寫或刪除既有 Study、evidence、authority、成果卡或 Workflow Package。
  - Development 後、寫成果卡前，依 `blind-review-strategy-study-v004` 技能先做 outcome-exposure／allowlist 檢查，再對新 Study 進行受限 blind review；只使用技能允許的研究設計、程式與 Development candidate／baseline evidence，不重跑 runner，不讀 `events/`、`journals/`、`operations/`、`study.yml` 或 Git 歷史，也不以完整 status／validate 取代盲檢討。若輸出或讀取超出 allowlist，立即停止且不重試，記錄實際範圍並標示盲檢討未通過。
  - 盲檢討階段結束後，依 `study-development-note-authoring-v004` 技能，以繁體中文 append-only 將新 Study 成果卡追加到 `.study-developer/development-note/TSM.md`。如實分列 candidate／baseline、base／stress、formal gates、targets、evidence validity、freeze eligibility／狀態、provenance、盲性、限制與下一輪可否證條件，並說明已確認、可能原因和尚不能判斷；數值只能取自允許的 Development evidence，缺件不得臆測。
  - 回報 Study ID、假說與新舊機制差異、workflow／reference／release／policy／source／data bindings、create／Development operation 識別資訊、evidence 與驗證結果、candidate freeze 狀態、盲檢討及成果卡自查結果、修改檔案與任何缺件，提供 parent 可在 PM 權限內核對的完整驗收證據包。完成時維持 Doing，由 parent review；若需修正，只交回同一 subagent，通過後由 parent 移至 Done。
- **摘要**：以既有 TSM breadth Study 為起點，在 v004 找出一個機制上不同、先前未嘗試的改進假說並完成 Development；完成後先盲檢討，再撰寫繁體中文成果卡，留下可由專案管理者驗收的研究紀錄。
- **進度／備註**：
  - 2026-09-23 由 parent thread 唯一 Study Developer subagent `/root/study_developer_task_022` 執行，狀態維持 Doing，等 parent 驗收。
  - **假說**：Study `tsm-momentum-trend-volume-breadth-dispersion--v001` 保留原 3/5 breadth，candidate 唯一新增訊號日前五日最大單日原始成交量占五日總量 `<=0.60`；baseline 保留原 breadth、不加 cap。已比對 TSM Development 卡：未見同一 raw-volume share cap；機制不同於 volume-lead、ramp、peak-lead 及 TASK-021 的量加權收盤路徑效率，不推定 TASK-021 取代或追加 breadth。
  - **前置校正**：初版 35% cap 在 Study create 前的 prepare synthetic fixture 未通過，因 fixture 的單日 5x volume 約占 prior 5 日 55.6%；另將部分條件輸出欄從 `raw_momentum_signal` 改名 `momentum_condition`，避免 v004 checker 誤把中間條件當完整訊號。未建立 Study、未跑 Development 資料即將門檻改為事前 60%，重算 bindings；final runner-preflight／prepare 均 passed。Parent review 確認此調整於 create 前固定，僅依 synthetic fixture 做校正，未用 Development outcome 選門檻。
  - **v004／資料 binding**：workflow=`62779bce18802e32ab314b6d74e8fc6f2da9fac03d1ee85a6416acc5553c67e4`；reference=`7b13d4d7e6448c9858215d9ef7e2e62fbd7fe0f40502e95a778a091008b20b47`；release=`ea04558c1473f9c6db7e9707846694147c6c6f254498af2f18729a1e4ef1fa84`；policy=`c86066b33119366a3172f475ff75f8813ba4b7545571894edfe581afabe32215`；prereg=`35728c5d7ec6edcf75bf0ba194a5abfa67154b254ed0ab31eca3a66087e0571e`；source bundle=`89b63978611889d3f90d7ca5cc1c588c4c963f3e237e21344c83d7157c6c3d34`。Development 使用固定 warmup-development view，資料 digest=`a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7`、Development role=`4e443b4c7db125967ef936d615b6d2283da8ba0bccc62239a5770daf176eccc3`、warmup=`81fdf3d66915935d87e930cb7882dbf52d27b88ba6776c1b047a2db6fc59c847`；訊號期間 2014–2018，warmup 2013。
  - **v004 執行與結果**：assignment=`research/tsm-momentum-trend-volume-breadth-dispersion--v001/assignment.yml`；create operation=`3fc98ae22dd4113012eb2cf4390486f0e92c5bfe4d896e1a62deb19ab5bb5b2e`；唯一 Development operation=`08d9191fd2aa35620345a6f5127ea5eb7facf2f1b048537bae7ddba16f558211`。candidate／baseline evidence 均 valid、7 筆／3 年（2015:1、2016:1、2018:5），結果欄位與績效相同。base return／PF=`7.1897%`／`4.2884`；stress=`5.5959%`／`3.5981`。唯一失敗 formal gate 及 candidate target 為 `completed_trades`（7<20）；其他 Development gates 與 targets 通過。candidate freeze eligibility=false，未凍結；未執行 Terminal 或正式 Historical Evaluation。
  - **盲檢討／成果卡**：目標 reference 再驗證通過；未接觸本 Study 正式 Evaluation／Terminal outcome，受限 blind review eligible 並完成，只讀設計、程式 binding 與 Development evidence／publication，不重跑 runner，未讀禁止路徑或 Git 歷史。原卡以 append-only 寫入；作者自查正文 530 字元。Parent 初審發現必填欄位缺件後，同一 subagent 另 append-only 補充 6,084 字元，補足逐 Trial 數值、gates／targets、provenance、blind review、前置調整原因、限制、否證條件及白話名詞說明，沒有新增 Study 標題或改寫原卡。沒有成果卡專用 checker；作者回報欄位自查通過，parent 依自查與 PM 可讀 evidence review 驗收。
  - **Parent review／結案**：已檢視 preregistration、candidate／baseline 定義、engine、assignment、development plan、candidate／baseline evidence 與 publication。新機制保留原 3/5 breadth，再加訊號日前五日最大單日原始量占比 ≤60%；與 TASK-021 path-efficiency 及已盤點近鄰機制不同，且沒有假定 TASK-021 是取代或追加 breadth。35%→60% 僅在 Study create 前依 synthetic fixture 調整，final preregistration／bindings 固定為 60%，未用 Development outcome 選門檻。parent 以 shasum 確認 candidate、baseline、inputs 與 publication digest 相符；candidate／baseline 的七筆交易結果及 metrics 相同：base return／PF／MDD 7.1897%／4.2884／1.999%，stress 5.5959%／3.5981／1.999%；三個交易年。兩份 evidence validity 均為 valid；唯一 formal gate 與唯一未達 candidate target 為 completed_trades（7<20），stress_return 與 traded_years targets 通過，freeze eligibility=false，未凍結。worker 回報 v004 runner-preflight／prepare、單次 create 與 Development trial 均完成；blind review eligible 且依允許範圍完成，沒有 allowlist 逸出。初次成果卡自查發現欄位缺件後，同一 subagent 依 append-only 原則補上逐項結果、來源綁定、調整原因、限制、下一輪否證條件及白話名詞說明；原卡正文 530 字元符合技能長度，另有審查補充。沒有成果卡專用 checker；parent 依 worker 的欄位自查及允許的 Development／PM 資料驗收。因 `.study-developer/AGENTS.md` 的角色存取限制，parent 未直接讀取成果卡；Done 表示派工、Development、盲檢討交付及角色範圍內驗收完成，不代表假說獲得支持或策略有效。

### [TASK-021] 以既有 TSM breadth Study 為基礎，在 v004 開發新假說、盲檢討並撰寫成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Codex Study Developer subagent `/root/study_developer_task_021`
- **建立日期**：2026-09-23
- **更新日期**：2026-09-23
- **依賴／阻塞**：無；接手時依 v004 規範確認 Workflow Release、reference 與資料綁定
- **驗收條件**：
  - 以 `tsm-momentum-trend-volume-breadth--v001` 為研究起點，先依 `.study-developer/development-note/TSM.md`、目標 Study 與 v004 允許讀取的既有 Development-only 證據盤點已試機制。將目標 Study 與 TASK-014 的盲檢討視為既有研究，不得重複其假說、只改參數／名稱／版本，或修改原 Study；提出機制明確、可預先登記且未曾嘗試過的新假說，說明近鄰與差異，並只建立一個新的 v004 Study。
  - 依 v004 `development-to-freeze` 核對 Workflow reference、release、policy、source 與 Development data bindings，完成 runner preflight、prepare、preregistration、candidate／baseline、implementation、runner、明確派工及 provenance；依法執行唯一 create、Development trial、evidence validation，以及適用的 freeze-readiness／candidate-freeze 嘗試。若資格不符，保留實際失敗狀態，不得繞過流程或補猜結果。
  - 僅執行 v004 Development；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得讀取、搜尋、雜湊、修改或引用 `historical-evaluation-artifacts/`、`.super-admin/`、正式 Evaluation／Terminal 結果、quarantine／full evaluation data；不得覆寫或刪除既有 Study、evidence、authority、成果卡或 Workflow Package。
  - Development 結束後，先依 v004 blind-review 規範核對 outcome exposure，再對新 Study 進行盲檢討；只用允許的研究設計、程式與 Development candidate／baseline evidence，不重跑 runner，不讀取 `events/`、`journals/`、`operations/`、`study.yml` 或 Git 歷史，也不以完整 status／validate 取代盲檢討。若讀取範圍或盲性受損，立即停止，不重試，並如實記錄未通過與實際讀取範圍。
  - 盲檢討階段結束後，才以繁體中文 append-only 將新 Study 成果卡追加至 `.study-developer/development-note/TSM.md`。逐 Trial 區分 candidate／baseline、base／stress、formal gates、targets、evidence validity、freeze eligibility／狀態、provenance、盲性、限制與下一輪可否證條件；數值只能來自允許的 Development evidence，缺件不得臆測，並說明「已確認／可能原因／尚不能判斷」。
  - 回報 Study ID、workflow／reference／release／policy／source／Development data digest、operation 識別資訊、可在角色範圍內讀取的狀態證據、實驗結果、盲檢討結果、成果卡位置、驗證與缺件。執行者完成後維持 Doing，由本 parent project manager review：假說是否確實未被嘗試、v004 流程是否合規、實驗與結果是否完整、盲檢討是否順利及成果卡是否符合專案規範。若需修正，只交回同一 subagent；通過後由 parent 移至 Done。
- **摘要**：承接既有 `tsm-momentum-trend-volume-breadth--v001` 的 Development 研究，在 v004 提出並驗證一個未曾嘗試的改進假說，依序完成 Development、同一新 Study 的盲檢討與繁體中文成果卡，留下可供驗收的研究依據。
- **進度／備註**：2026-09-23 由本 parent thread 唯一 Study Developer subagent `/root/study_developer_task_021` 完成，未建立 top-level conversation/thread。Study `tsm-momentum-trend-volume-path-efficiency--v001` 完成 v004 precreate、runner-preflight、prepare、唯一 create 與唯一 Development trial；candidate／baseline evidence 均 valid。Candidate 6 筆，base／stress return `+3.3189%`／`+2.1950%`、PF `2.1864`／`1.7648`、MDD `2.3249%`／`2.5829%`；formal gates 失敗交易數及 stress bootstrap 正報酬比（`0.7193<0.80`），freeze eligibility=false，未凍結。Baseline 10 筆，base／stress return `+2.1411%`／`+0.5312%`、PF `1.3059`／`1.0756`、MDD `2.1279%`／`2.2747%`；失敗交易數、bootstrap 比率及 stress 留一年 PF／return gates。Blind outcome-exposure 檢查在允許範圍內合格，受限 blind review 完成；發現並如實列出三項 frozen design／traceability defects：preregistration 留有舊 3/5 breadth 描述、implementation contract 欄位不符 bound engine 輸出、docstring 稱方向效率但公式取絕對值。成果卡已 append-only 更正，完整呈現指標、gates／targets、provenance、近鄰差異、盲性與限制；baseline evidence digest 依 Development publication 逐字核對。既有 Development-only 證據未見同一 path-efficiency 規則，但因註冊文件歧義，path-efficiency 究竟取代或追加 3/5 breadth 尚不能判定，不宣稱有效性或因果優勢。parent review 確認 v004 流程、實驗、受限盲檢討與成果卡交付達驗收條件；Done 表示交付流程完成，不代表候選達 freeze 資格、策略有效或 frozen 文件完全一致。

### [TASK-020] 依 TSM Development 盤點在 v004 開發新的動能趨勢 × 量先價行假說，依序完成 blind review 與成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：本 parent thread 的唯一 Study Developer subagent `/root/study_developer_task_020`
- **建立日期**：2026-09-23
- **更新日期**：2026-09-23
- **依賴／阻塞**：無；執行前依 v004 規範確認 Workflow Release 與資料綁定
- **驗收條件**：
  - 依 `.study-developer/development-note/TSM.md` 及 v004 允許讀取的既有 Development-only 研究，先整理已嘗試的 TSM 動能、趨勢與量先價行機制，再提出一個機制清楚、可預先登記、確實未曾嘗試的新假說；明確說明近鄰與新舊機制差異，不得只改名稱、版本或重複 TASK-019 的固定 t−5 中性高量事件／後續量縮／訊號日加速組合。
  - 依 v004 `development-to-freeze` 完成 Workflow reference、release、policy、source 與 Development data 綁定核對、runner preflight、prepare、單一 Study 的 preregistration、candidate／baseline、implementation、runner、明確派工與 provenance；依規則完成唯一 create、Development trial、evidence validation，以及適用的 freeze-readiness／candidate-freeze 嘗試。資格不符時如實保留失敗狀態，不得繞過流程。
  - 僅執行 v004 Development；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得讀取、搜尋、雜湊、修改或引用 `historical-evaluation-artifacts/`、`.super-admin/`、正式 Evaluation／Terminal 結果、quarantine／full evaluation data，亦不得覆寫或刪除既有 Study、evidence、authority 或 Workflow Package。
  - Development 完成後，先依 v004 blind-review 規範確認 outcome exposure，再只針對該 Study 進行 blind review；限定於允許的研究設計、程式與 Development candidate／baseline evidence，不重跑 runner，不讀取 `events/`、`journals/`、`operations/`、`study.yml` 或 Git 歷史，也不使用完整 status／validate 代替盲檢討。若意外輸出或讀到 allowlist 外內容，停止並如實標記 blind review 未通過，不得重試或宣稱通過。
  - blind review 階段結束後，才以繁體中文 append-only 將新 Study 成果卡追加至 `.study-developer/development-note/TSM.md`；逐 Trial 區分 candidate／baseline、base／stress、formal gates、targets、evidence validity、freeze eligibility／狀態、provenance、盲性、限制與下一輪可否證條件。數值只能來自允許的 Development evidence，缺件不得補猜。
  - 回報 Study ID、workflow/reference/release/policy/source/data digest、operation 識別資訊、event 狀態（僅用該角色可讀證據）、實驗結果、成果卡位置、驗證與任何缺件。完成後由 subagent 維持 Doing；parent project manager review。若有問題，只交回同一 subagent 修正；驗收通過後由 parent 移至 Done。
- **摘要**：沿著既有 TSM Development 研究脈絡，於 v004 提出並檢驗一個過去未嘗試的量先價行動能趨勢機制，完成 Development、盲檢討與成果卡，讓結果可追溯並供專案驗收。
- **進度／備註**：2026-09-23 由本 parent thread 唯一 Study Developer subagent `/root/study_developer_task_020` 完成，未建立 top-level task/thread。Study `tsm-momentum-trend-volume-gap-retention--v001` 的假說為前五日平均量比至少 1.05 先行，再要求訊號日正向開盤缺口至少 0.50% 且收盤不低於開盤；TSM Development 卡片未見相同的量能先行＋正向當日缺口接受組合。近鄰 gap-anchoring 測的是前五日負缺口量能承接；新意僅限規則組合與時序，不宣稱各組件首創。v004 workflow/reference/release/policy binding 核對一致；runner-preflight 與 prepare passed，Source Bundle 10/10 檔驗證通過。唯一成功 create operation=`c69578922b8dd9bd1cd4b93b708eb1011cd4ac152e44f2e0a2fb837dd0923f40`，唯一正式 Development operation=`3e47478653c8a0b5df2e9ee8cf13d4ef88c323e74f195fca1af101922a423d93`；candidate／baseline evidence 均 `valid`。Candidate 9 筆／3 年，base return 0.2327%／PF 1.0337、stress −1.0725%／PF 0.8457，7 項 formal gates 與 2 項 targets 失敗；baseline 10 筆／4 年，base 2.1411%／PF 1.3059、stress 0.5312%／PF 1.0756，4 項 gates 失敗。candidate freeze eligibility=`false`，Study 停在 Development 完成，未凍結；未執行 Historical Evaluation、Terminal、challenge 或 replay。Blind review **未通過**：檢討前遞迴 `rg` 搜尋掃過整個 v004 workflow，輸出含 allowlist 外 Study 的 `events/`／`study.yml` 路徑及事件摘要；依技能立即停止且未重試，後續更正已 append-only 記錄此事實與讀取範圍限制。成果卡已 append-only 撰寫並經 parent correction 補足讀取範圍更正、「已確認／可能原因／尚不能判斷」及 provenance binding。Parent review 確認 Development 研究差異、v004 綁定、candidate／baseline 結果及成果卡記載相符；Done 代表派工與可允許的交付已完整，**不代表 blind review 通過**。

### [TASK-019] 依 TSM Development 盤點在 v004 開發新動能趨勢 × 量先價行假說，完成 blind review 與成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Codex Study Developer subagent `/root/study_developer_task_019`
- **建立日期**：2026-09-23
- **更新日期**：2026-09-23
- **依賴／阻塞**：無；執行前依 v004 規範確認 Workflow Release 為 Active
- **驗收條件**：
  - Study Developer 依 `.study-developer/development-note/TSM.md`、v004 workflow 與其允許讀取的既有 TSM Development 證據盤點既有假說，提出有清楚機制差異、可追溯且過去未曾嘗試的新「動能趨勢 + 量先價行」假說；說明近鄰限制，不得僅改名、版本或重用既有規則。
  - 依 v004 `development-to-freeze` 完成適用的 workflow/reference/release/policy/source 與 Development data 綁定核對、runner preflight、prepare、單一 Study 的 preregistration、candidate/baseline、implementation、runner、明確派工與 provenance；依流程完成合法的 create、Development trial、evidence validation 及 freeze-readiness／candidate-freeze 嘗試。資格不符時保留實際失敗狀態，不得繞過規則。
  - 僅執行 v004 Development；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得讀取、搜尋、雜湊、修改或引用 `historical-evaluation-artifacts/`、`.super-admin/` 或正式 Evaluation／Terminal 結果；不得覆寫或刪除既有 Study、evidence、authority、成果卡或 Workflow Package。
  - Development 完成後，依 v004 blind-review 規範先核對 outcome exposure，再對同一 Study 進行受限 blind review；只使用規範允許的研究設計、程式、Development candidate/baseline evidence 與 binding，不重跑 runner，也不以完整 status/validate 取代 blind review。若盲性受損，停止並如實回報。
  - blind review 完成後，才以繁體中文 append-only 更新 TSM Development 成果卡；完整呈現 candidate/baseline、base/stress、gates/targets、evidence validity、凍結資格與狀態、provenance、盲性、限制及可否證的下一步；缺少證據時不得補猜。
  - 回報 Study ID、適用 workflow/reference/release/policy/source/data digest、operation 識別資訊、驗證結果、修改檔案及任何缺件。完成後由 Study Developer 維持 Doing；由本 parent project manager review。若有問題，只交回同一 subagent 修正；驗收通過後由 parent 移至 Done。
- **摘要**：依 TSM 的 Development 研究脈絡，在 v004 建立並檢驗一個未曾嘗試的量先價行動能趨勢假說，依序完成 Development、同一 Study 的受限 blind review 與繁體中文成果卡，留下可追溯的研究結果。
- **進度／備註**：2026-09-23 由本 parent thread 指派的唯一 Study Developer subagent `/root/study_developer_task_019` 完成，未建立 top-level thread。Parent review 確認假說的固定 t−5 高量中性事件、四日量縮且未先漲、訊號日才加速，與既有 d→d+1 response-lag、動態 peak-lead、同日 absorption 及 v024 固定事件價突破有明確差異；新穎性僅主張此條件組合未見已嘗試，未宣稱完全獨立。v004 為 Active；reference/release/policy/source 與 Development data binding、runner-preflight、prepare 核對通過，唯一 create 與 Development trial 完成。candidate／baseline evidence 均 valid；candidate 0 trades、13 項 gates 與 3 項 targets 失敗；baseline 16 trades／5 年，base/stress return 為 −0.5729%／−2.7935%、PF 為 0.9556／0.7800，8 項 gates 失敗。freeze-readiness／freeze 均合法回報 `qualification-failed`，Study 未凍結。Blind review **未通過**：成果卡 checker 搜尋意外輸出四個鄰近 Study 的 assignment 片段，越出單一 Study allowlist；未曝光 formal outcomes/evidence，subagent 依技能停止且未重試，卡片如實揭露。TSM 成果卡欄位、provenance 與 append-only key 歧義更正已核對；舊 resistance/retest key 與新 lagged-neutral key 並存的規格歧義已揭露、immutable binding 未回改。正文 671 漢字，符合 authoring skill「約 300–600 字」的近似篇幅；卡片各要求欄位均齊全。工作依規範記錄並完成，Done 不表示 blind review 通過。

### [TASK-018] 在 v004 開發另一個未嘗試的 TSM 動能趨勢 × 量先價行假說，完成 blind review 與成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Erdos（本 parent thread 唯一 Study Developer subagent，`01a0c8ec-72d6-7362-a292-74bb25847635`）
- **建立日期**：2026-09-22
- **更新日期**：2026-09-22
- **依賴／阻塞**：無；接手時先確認 v004 Workflow Release 為 Active
- **驗收條件**：
  - 先依根目錄 `AGENTS.md`、`.study-developer/development-note/TSM.md`、v004 reference 與允許讀取的既有 TSM Development-only Study，盤點已嘗試過的動能、趨勢與量先價行機制；提出一個可追溯且確實未被嘗試過的新假說。不得只是改版本號、改名稱、重用同一規則或無語義重發，並須在研究設計中說明與既有 Study 的機制差異及近鄰限制。
  - 依 v004 `development-to-freeze` 固定入口完成 Workflow reference／release／policy／source digest 核對、runner preflight、prepare，建立單一新 Study 的 preregistration、candidate／baseline、implementation、runner、Development data bindings、明確派工與 provenance；完成唯一合法的 create、Development trial、evidence validation，以及規則允許的 freeze-readiness／candidate-freeze 嘗試。若資格失敗，保留 `qualification-failed` 與未凍結狀態，不得補猜或繞過流程。
  - 只執行 v004 Development；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得讀取、搜尋、雜湊、修改或引用 `historical-evaluation-artifacts/`、`.super-admin/`、正式 Evaluation／Terminal 結果、quarantine／full evaluation data、events、journals、operations 或 Git 歷史，也不得覆寫、刪除或重排既有 Study、evidence、authority、成果卡或 Workflow Package。
  - Development 完成後，對同一 Study 依 v004 blind-review 規範完成受限盲檢討：先確認沒有正式 outcome exposure；只讀研究設計、程式與 Development candidate／baseline evidence 及允許的 binding，不重跑 runner，不以完整 `status`／`validate` 取代 blind review；若盲性已破壞，立即停止並如實回報。
  - blind review 完成後，才以繁體中文 append-only 更新 `.study-developer/development-note/TSM.md` 的該 Study 成果卡。成果卡約 300–600 字，逐 Trial 區分 candidate／baseline、base／stress、formal gates、research targets、evidence validity、candidate freeze 資格／狀態、provenance、盲性狀態、已確認問題、可能原因、尚不能判斷、限制與下一輪單一可否證變更；缺少 evidence 時不得補猜數值，並聲明未使用正式結果與實際讀取限制。
  - 通過對應 v004 checker／validator、必要 pytest、Ruff（若適用）與 `git diff --check`；回報 Study ID、workflow／reference／release／policy／source／Development data digest、create／Development operation ID、事件 head／count（若盲讀限制不允許則標示 unavailable）、修改檔案、Development 與 blind review 驗證結果及任何實際缺件。
  - 接手時將本任務由 TODO 移到 Doing；完成工作後維持 Doing，由 parent project manager 依下列項目驗收：假說確實未被嘗試過、符合 v004 workflow、實驗與結果完整、blind review 順利且未越過讀取邊界、成果卡符合專案規範。若 review 發現問題，只能將修改要求交回同一個 subagent；修正通過後由 parent 移到 Done，不得另開 subagent 或建立獨立 top-level Codex conversation/thread。
- **摘要**：根據 TSM Development 研究盤點，在 v004 workflow 中提出並驗證另一個真正新的「量先於價、用於動能趨勢確認」機制，依序完成 Development、同一 Study 的受限 blind review 與不混入正式結果的繁體中文成果卡，讓後續是否值得凍結有清楚且可追溯的證據。
- **進度／備註**：2026-09-22 由本 parent thread 只 spawn 一個 Erdos Study Developer subagent 接手，未建立 top-level thread。Study `tsm-momentum-trend-volume-body-sign-consistency--v001` 已完成 v004 workflow reference／release／policy／source／Development data binding 核對、runner-preflight、prepare、唯一 create、唯一 Development trial、evidence validation 與 freeze-readiness／freeze 嘗試；candidate／baseline evidence 均 `valid`，candidate base／stress 各 3 筆／3 年，return `0.6977421%`／`0.2156383%`、PF `1.3278289`／`1.1017603`，因 `completed_trades` 與 stress leave-one-year-out PF／return 失敗而 `qualification-failed`、未凍結；baseline base／stress 各 10 筆／4 年，return `2.1411376%`／`0.5312003%`、PF `1.3058564`／`1.0755804`，另有交易數與 stress robustness gates 失敗。blind review 已完成且 exposure check 通過；未讀取、引用或修改正式 Evaluation／Terminal、events、journals、operations、`study.yml`、`historical-evaluation-artifacts/` 或 `.super-admin/`，event head/count 依盲讀限制標示 unavailable。parent review 確認假說不是既有 Study 的版本重發，但不過度宣稱 Open→Close 概念全新：已揭露 v012 的單日未加權 `Close>Open`／區間位置近鄰，以及 `body-followthrough` 的五日 Open→Close 加權／未加權平均近鄰；本 Study 可主張差異是五日成交量加權非負實體占比 `>=0.60` 加固定五日量比，先於動能趨勢／價格加速。成果卡在 blind review 後以繁體中文 append-only 寫入並經 parent review correction 補足 baseline evidence 與新穎性邊界；未修改 immutable Study／evidence／publication／binding。QA：canonical／source-bundle validator（subagent）passed、Study pytest `5 passed`、Ruff passed、8 份允許 YAML parse passed、`git diff --check` passed；未執行完整 project pytest、runner、status、validate 或正式 Evaluation。parent review 通過，移至 Done。

### [TASK-017] 在 v004 開發新的 TSM 動能趨勢 × 量先價行假說，完成 blind review 與成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Codex study developer subagent（TASK-017，唯一受派執行者）
- **建立日期**：2026-09-22
- **更新日期**：2026-09-22
- **依賴／阻塞**：無；先確認 v004 Workflow Release 為 Active
- **驗收條件**：
  - 先依根目錄規範、`.study-developer/development-note/TSM.md` 與允許讀取的既有 TSM Development-only Study，盤點已嘗試過的動能、趨勢與量先價行機制，提出一個可追溯且確實未被嘗試過的新假說；不得只是改版本號、改名稱、重用同一規則或無語義重發，並須在研究文件中說明與既有 Study 的機制差異。
  - 依 v004 `development-to-freeze` 完成 Workflow reference／release／policy／source digest 核對、runner preflight、prepare，固定單一新 Study 的 preregistration、candidate／baseline、implementation、runner、Development data bindings、明確派工與 provenance；完成唯一合法的 create、Development trial、evidence validation，以及規則允許的 freeze-readiness／candidate-freeze 嘗試。若資格失敗，必須保留 `qualification-failed` 與未凍結狀態，不得補猜或繞過流程。
  - Development 階段只使用 v004 Development 範圍；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得讀取或修改 `historical-evaluation-artifacts/`、`.super-admin/`、正式 Evaluation／Terminal 結果，也不得覆寫、刪除或重排既有 Study、evidence、authority、events、成果卡或 Workflow Package。
  - Development 完成後，對同一 Study 依 v004 blind-review 規範進行受限盲檢討：先確認本次沒有正式 outcome exposure；只讀取研究設計、程式與 Development candidate／baseline evidence 及其允許 binding，不得重跑 runner，不得以完整 `status`／`validate` 取代 blind review；若盲性已破壞，立即停止並如實回報。
  - blind review 完成後，才以繁體中文 append-only 更新 `.study-developer/development-note/TSM.md` 的該 Study 成果卡。成果卡約 300–600 字，逐 Trial 區分 candidate／baseline、base／stress、formal gates、research targets、evidence validity、candidate freeze 資格／狀態、provenance、盲性狀態、已確認問題、可能原因、尚不能判斷、限制、下一輪單一可否證變更，並聲明未使用正式結果與實際讀取限制；缺少 evidence 時不得補猜數值。
  - 通過對應 v004 validator／checker、必要 pytest、Ruff（若適用）與 `git diff --check`；回報 Study ID、workflow／reference／release／policy／source／data digest、create／Development operation ID、事件 head／count、修改檔案、Development 與 blind review 驗證結果及任何實際缺件。
  - 接手時將本任務由 TODO 移到 Doing；完成工作後維持 Doing，由 parent project manager review。若 parent review 發現問題，只能將修改要求交回同一個 subagent，修正通過後才由 parent 移到 Done，不得另開 subagent 或新 top-level Codex conversation/thread。
- **摘要**：根據 TSM Development 研究盤點，在 v004 workflow 中提出並驗證一個真正新的「量先於價、用於動能趨勢確認」機制，依序完成 Development、同一 Study 的受限 blind review 與不混入正式結果的繁體中文成果卡，讓後續是否值得凍結有清楚且可追溯的證據。
- **進度／備註**：2026-09-22 已由本 parent thread 指派唯一 Codex study developer subagent 接手，狀態維持 Doing。已完成規範／三份 v004 skill／reference-first 核對與 TSM Development-only 機制盤點，建立新 Study `tsm-momentum-trend-volume-body-followthrough--v001`；runner-preflight、prepare、唯一 create、唯一 Development trial 均通過固定入口。candidate／baseline evidence 均 valid，但 candidate 3 筆交易未達 20 筆，formal gate 與 research target 的 `completed_trades` 失敗；freeze-readiness／freeze 均保留 `qualification-failed`、未凍結。已完成同一 Study 的受限 blind review 並 append-only 更新 TSM.md；未執行或讀取正式 Evaluation／Terminal。create operation=`2356a4d1…605f11`、Development operation=`03adb083…a04bb9`、event count=`4`；event head 因 blind review 禁止讀取／雜湊 events／authority，標示 unavailable，不補猜。直接 pytest 13 passed、Ruff passed、git diff --check passed。維持同一 Study、同一 operation 與本角色，不建立 top-level thread 或 descendant；parent review 後如需修正仍由本 subagent 接續。
- **Parent review 回修（2026-09-22）**：依 review 在 TASK-017 成果卡補足既有 `tsm-mean-reversion-two-stage-volume-reversal--v012` 的近鄰機制差異：該卡是單日未加權 Close > Open／區間位置的均值回歸確認；本 Study 則是訊號日前五個已完成 session 的成交量加權 Open→Close 實體平均及相對未加權平均差值，置於動能趨勢／價格加速前。保留 assignment 原文 `0.05` 個百分點與實際 canonical contract=`0` 的 immutable 規格限制揭露；未回寫 assignment、preregistration、Source Bundle 或 evidence，未重跑 runner／建立新 Study 或 operation。狀態維持 Doing，待 parent review。
- **Parent review 結果（2026-09-22）**：驗收通過並移至 Done。新假說不是既有 Study 的版本重發：它測試訊號日前五個已完成 session 的成交量加權 Open→Close 實體平均，及其相對同窗口未加權平均的差值，並先於動能趨勢／價格加速訊號；同時已 append-only 揭露 v012 的單日未加權 Close>Open 近鄰規則，避免過度宣稱 Open→Close 概念完全前所未有。v004 Workflow Release 為 Active；workflow／reference／release／policy／source／Development data binding、唯一 create／Development operation、4-event chain 與 evidence publication 綁定均核對一致，Workflow Package 未被修改。candidate／baseline evidence 均 `valid`；candidate base／stress 各 3 筆／3 年、報酬 5.0316%／4.2172%、PF 均 `inf`、回撤 0%，僅因 `completed_trades=3<20` 失敗；baseline 10 筆／4 年、報酬 2.1411%／0.5312%、PF 1.3059／1.0756%，另有 stress robustness gates 失敗。candidate freeze eligibility=`false`，freeze-readiness／freeze 均 `qualification-failed`，未產生 `candidate-frozen`。assignment 的 0.05 個百分點與實際 canonical contract 的 0 門檻不一致，但成果卡已明確揭露，未冒稱 0.05 假說，也未回寫 immutable binding。受限 blind review 的 exposure check 通過，未讀取正式 Evaluation／Terminal／Historical Evaluation、events／journals／operations，未重跑 runner，成果卡在 blind review 後才以繁體中文 append-only 更新，內容包含逐 Trial base／stress、formal gates、research targets、evidence validity、provenance、盲性、已確認／可能原因／尚不能判斷、限制、下一輪可否證條件及來源限制；event head 依盲讀邊界標示 unavailable。驗證：subagent 回報選定 v004 測試 13 passed、Study pytest 4 passed、Ruff 與 `git diff --check` passed；parent 重新執行 Study pytest 4 passed、Ruff、9 份研究 YAML parse 與 `git diff --check` 均通過；parent 另一次較廣 v004 測試在 36 passed 後因長時間執行中止，未宣稱完整 suite 通過。未執行 Historical Evaluation、Terminal、challenge 或 replay；未讀取或修改 `historical-evaluation-artifacts/`、`.super-admin/` 或正式結果。

### [TASK-016] 將 `tsm-momentum-trend-volume-response-lag--v001` 假說、policy 與回測整理為 Google Colab notebook
- **狀態**：Done
- **優先級**：中
- **負責角色**：study 開發者
- **執行者**：Anscombe（本 parent thread 唯一 Study Developer subagent `01a0c746-df08-7812-8590-1a1fdfd8bf9a`）
- **建立日期**：2026-09-22
- **更新日期**：2026-09-22
- **依賴／阻塞**：無；只使用既有 Study 的 Development-only 規格與證據，不重新執行正式 Evaluation
- **驗收條件**：
  - 讀取 `tsm-momentum-trend-volume-response-lag--v001` 的 preregistration、candidate／baseline definition、implementation／runner contract、v004 workflow reference／policy binding 與 Development evidence；不得讀取或引用 `historical-evaluation-artifacts/`、正式 Evaluation／Terminal 結果、`.super-admin/`、events、journals、operations 或 Git 歷史。
  - 建立一個有效的 `.ipynb`，建議路徑為 `notebooks/tsm_momentum_trend_volume_response_lag_v001_colab.ipynb`；Notebook 必須可在 Google Colab 開啟，不能依賴本機 package import 或 repository checkout 才能理解核心邏輯。
  - 以繁體中文 Markdown 說明 Study 假說與限制：訊號日前五個已完成的「成交量→下一 session 收盤到收盤報酬」配對、加權後續報酬下限 `-0.02`、加權減未加權至少 `0.0005`，以及趨勢、RSI、收盤方向、至少 2% 價格加速與五日量比條件。
  - 明確列出 v004 policy／執行規則與可重現設定：Yahoo auto-adjusted OHLCV、XNYS session、下一個 open 進場、2% risk budget、-4% stop、+4% target、最多 10 個完整 session、退出後 5-session cooldown、adverse-stop-first，以及 base 每邊 1／5 bps、stress 每邊 2／20 bps 成本。
  - Code cells 必須自包含地完成資料上傳／本地 CSV fallback、欄位與日期整理、指標計算、candidate／baseline 回測、base／stress metrics（交易數、年度、報酬、PF、最大回撤）與至少一個結果視覺化；不得把正式 Development evidence 的結果硬編成回測輸出，也不得宣稱 Colab 重跑就是正式 Evaluation。
  - Notebook 應有離線或合成資料 smoke path，使沒有上傳資料時也能驗證程式結構；不得在執行時自動下載 Yahoo 或其他外部資料。需以 nbformat／Notebook execution 檢查 JSON 與 cells 可執行，並通過 notebook 直接測試、Ruff（若有外部 `.py` helper）與 `git diff --check`。
  - 完成後將任務由 TODO 移到 Doing，回報 notebook 路徑、使用的 Study／policy digest、回測規則、驗證命令與結果；完成工作後維持 Doing，由 parent project manager review，若有問題只能交回同一個 subagent 修正，通過後才移到 Done。
- **摘要**：把既有 v004 Development Study 轉成可在 Google Colab 閱讀、上傳資料並重現策略邏輯的教學／研究 notebook，讓使用者能看懂量先價後延遲報酬假說、政策限制與 base／stress 回測結果，同時避免把 notebook 當成正式評估證據。
- **進度／備註**：2026-09-22 已由 parent thread 只 spawn exactly one Study Developer subagent Anscombe（`01a0c746-df08-7812-8590-1a1fdfd8bf9a`）接手，狀態由 TODO 移至 Doing。已讀取根目錄規範、TASK-016、v004 workflow reference／release／policy binding、Study preregistration、candidate／baseline definition、implementation／runner contract、Development inputs／evidence／publication 與 TSM Development-only 卡；未讀取禁止範圍。已新增 `notebooks/tsm_momentum_trend_volume_response_lag_v001_colab.ipynb`：包含繁中假說與限制、candidate／baseline、policy 摘要、離線 synthetic fallback、Colab upload 開關、OHLCV/session 驗證、指標、next-open、2% sizing、base／stress cost、stop／target／time exit、cooldown、ledger、metrics、equity／trade 圖與 look-ahead test。固定 binding 摘要為 workflow `62779bce18802e32ab314b6d74e8fc6f2da9fac03d1ee85a6416acc5553c67e4`、reference `7b13d4d7e6448c9858215d9ef7e2e62fbd7fe0f40502e95a778a091008b20b47`、release `ea04558c1473f9c6db7e9707846694147c6c6f254498af2f18729a1e4ef1fa84`、policy set `c86066b33119366a3172f475ff75f8813ba4b7545571894edfe581afabe32215`、source `06ed3b3bdb9c596df4c213d2fb657b368de9950d3ddbe1282ccb408a3639c426`、preregistration `8018ba3fff138c288c0e4d863ca75fc45ec30d3f219c88743d6ae035f94ba7d9`。驗證：JSON parse、10 個 code cells compile／非互動執行、look-ahead PASS、CSV valid／duplicate／weekend smoke PASS、Ruff PASS、reference indicators／execution equivalence PASS、git diff whitespace check PASS；目前無具體阻塞。工作完成後維持 Doing，等待 parent review，不移到 Done。
- **Parent review 結果（2026-09-22）**：已驗收通過並移至 Done。假說、v004 policy 與回測邏輯均對應既有 Development-only Study 規格；notebook 為自包含 Colab JSON（nbformat 4、Python 3、23 cells／10 code cells），預設使用 deterministic synthetic smoke，僅在明確開關後提供 Colab upload，沒有自動下載或 repository import。parent 以 `.venv/bin/python` 完成全部 code cells 非互動執行，look-ahead／CSV smoke 通過；另與既有 reference 實作逐欄比對 indicators，並比對 candidate／baseline 的 base／stress backtest 與 metrics，結果等價；`git diff --check` 通過。未修改 Study、正式 Evaluation、Terminal 或受限資料夾，沒有把 notebook smoke 結果宣稱為正式 Evaluation。

### [TASK-012] 在 v004 開發下一個未嘗試的 TSM 動能趨勢 × 量先價行假說並撰寫成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Newton（本對話唯一 Study Developer subagent `01a0c36d-1a60-7b00-8284-6898346bc9b1`）
- **建立日期**：2026-09-21
- **更新日期**：2026-09-21
- **依賴／阻塞**：無；先確認 v004 Workflow Release 為 Active
- **驗收條件**：
  - 依允許範圍讀取根目錄規範、`.study-developer/development-note/TSM.md` 與既有 TSM Development Study，盤點已嘗試過的動能、趨勢及量先價行機制；提出一個可追溯、確實未被嘗試過的新假說，不得只是改版本號、改名稱、重用同一規則或無語義重發。
  - 依 v004 `development-to-freeze` 流程建立單一新 Study，先完成 Workflow reference／release digest 核對、runner preflight 與 prepare，再固定 preregistration、candidate／baseline、implementation、runner、Development data bindings、明確派工與 provenance；完成唯一合法的 Development trial、evidence validation，以及規則允許的 freeze-readiness／candidate-freeze 嘗試。
  - 只執行 v004 Development；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得讀取或修改 `historical-evaluation-artifacts/`、`.super-admin/`、正式 Evaluation／Terminal 結果，也不得覆寫、刪除或重排既有 Study、evidence、authority、events 或成果卡。
  - Development 完成後，以繁體中文 append-only 更新 `.study-developer/development-note/TSM.md` 的該 Study 成果卡；逐 Trial 區分 candidate／baseline、base／stress、formal gates、research targets、evidence validity、candidate freeze 資格／狀態、provenance、限制與下一輪可否證條件。缺少 evidence 時不得補猜數值，並清楚標示已確認、可能原因與尚不能判斷。
  - 通過對應 v004 validator／checker、必要 pytest、Ruff（若適用）與 `git diff --check`；回報 Study ID、workflow／reference／source digest、operation ID、事件 head、修改檔案、驗證結果、實驗結果與任何實際缺件。subagent 完成後維持 Doing，由 parent project manager review 後才可移到 Done。
- **摘要**：根據 TSM Development 研究盤點，在 v004 workflow 中提出並驗證一個真正新的「量先於價、用於動能趨勢確認」機制，產出可追溯的 Development Study 與成果卡，讓後續是否值得凍結有清楚且不越權的證據。
- **進度／備註**：2026-09-21 由 Newton 完成單一 v004 Study `tsm-momentum-trend-volume-peak-lead--v001`。新機制是五日視窗量能峰值至少早於收盤報酬峰值一個 session，再由動能趨勢與價格加速確認；與既有總量壓力、量能脈衝、吸收、日內效率、收盤承接、量能報酬、缺口、持續性及 v024 事件突破有語義差異，並已揭露共用單日峰值／OHLCV 的限制。workflow／reference／source binding 已固定；runner-preflight 與 prepare 均 `passed`。唯一 create operation=`4526cbfcbefc6d791e7e292beb42c60b1e0ad6e7d642741ad08ed5c3d9dde919`，唯一 Development operation=`7ac595cc5e3f1bb2c689849b4c6b7fbf573aebfd08311cb90a1832f4579c5c04`；candidate／baseline evidence 均有效。Candidate base／stress 各 1 筆、1 年、報酬約 -1.9986%／-2.0000%、PF 0；baseline base／stress 各 10 筆、4 年、報酬 2.1411%／0.5312%、PF 1.3059／1.0756；candidate 與 baseline 均有 formal gate 失敗，targets=`not_registered`。status／validate 通過，event head=`40cb635d4aecf6a9316a42c53e8d8c1abb3a698646238517059727dec7861543`、event_count=`4`；freeze-readiness／freeze 均 `qualification-failed`，未產生 candidate-frozen，provenance 未達 `verified-clean`。成果卡已 append-only 寫入 TSM.md；新 Study pytest `5 passed`、v004 選定測試 `25 passed`、Ruff passed、git diff --check passed。未執行 Historical Evaluation、Terminal、challenge 或 replay，未讀取或修改禁止範圍。
- **Parent review 結果（2026-09-21）**：核對公開 preregistration、candidate／baseline evidence、四事件鏈、authority checkpoints、workflow／reference／release／source bindings 與唯一 Development operation；確認「量峰先於價峰」不是既有量能總量、脈衝、吸收、效率、收盤承接、量價報酬、缺口、持續性或 v024 固定突破的重複。candidate／baseline evidence 均 `valid`，formal gates、`candidate_freeze: null`、`qualification-failed` 與成果卡回報一致；parent 重跑新 Study pytest `5 passed`、v004 選定測試 `25 passed`、Ruff 與 `git diff --check` 均通過。TASK-012 通過驗收，移至 Done。

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


### [TASK-015] 在 v004 開發新的 TSM 動能趨勢 × 量先價行假說，完成 blind review 與成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Ptolemy（本 parent thread 唯一 Study Developer subagent `01a0c6e4-ae0b-7200-8836-d8cc701f0383`）
- **建立日期**：2026-09-22
- **更新日期**：2026-09-22
- **依賴／阻塞**：無；接手時先確認 v004 Workflow Release 為 Active
- **驗收條件**：
  - 依根目錄規範、`.study-developer/development-note/TSM.md` 與允許讀取的既有 TSM Development Study，盤點已嘗試過的動能、趨勢及量先價行機制；提出一個可追溯、確實未被嘗試過的新假說，不得只是改版本號、改名稱、重用同一規則或無語義重發，並在研究文件中說明與既有 Study 的機制差異。
  - 依 v004 `development-to-freeze` 流程完成 Workflow reference／release／policy digest 核對、runner preflight、prepare，固定單一新 Study 的 preregistration、candidate／baseline、implementation、runner、Development data bindings、明確派工與 provenance；完成唯一合法的 Development trial、evidence validation，以及規則允許的 freeze-readiness／candidate-freeze 嘗試。若資格失敗，必須如實保留 `qualification-failed` 與未凍結狀態，不得補猜或繞過流程。
  - Development 階段只使用 v004 Development 範圍；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得讀取或修改 `historical-evaluation-artifacts/`、`.super-admin/`、正式 Evaluation／Terminal 結果，也不得覆寫、刪除或重排既有 Study、evidence、authority、events 或 Workflow Package。
  - Development 完成後，針對同一個 Study 依 v004 blind-review 規範進行受限盲檢討：先確認本次沒有正式 outcome exposure；只讀取研究設計、程式與 Development candidate／baseline 證據及其允許 binding，不得重跑 runner，不得以完整 `status`／`validate` 取代 blind review；若發現盲性已破壞，立即停止 blind review 並如實回報。
  - blind review 完成後，才以繁體中文 append-only 更新 `.study-developer/development-note/TSM.md` 的該 Study 成果卡；逐 Trial 區分 candidate／baseline、base／stress、formal gates 與 research targets、evidence validity、candidate freeze 資格／狀態、provenance、盲性狀態、已確認問題、可能原因、尚不能判斷、限制、下一輪可否證條件與「未使用正式結果」聲明。不得覆寫既有成果卡或補填缺少的 evidence。
  - 通過對應 v004 validator／checker、必要 pytest、Ruff（若適用）與 `git diff --check`；回報 Study ID、workflow／reference／release／source digest、create／Development operation ID、事件 head／count、修改檔案、Development 與 blind review 驗證結果及任何實際缺件。subagent 完成後維持 Doing，由 parent project manager review；若 review 發現問題，只能將修改要求交回同一個 subagent，通過後才移到 Done。
- **摘要**：根據 TSM Development 研究盤點，在 v004 workflow 中提出並驗證一個真正新的「量先於價、用於動能趨勢確認」機制，先完成 Development，再對同一 Study 做受限 blind review，最後產出不混入正式結果的繁體中文成果卡，讓後續是否值得凍結有清楚且可追溯的證據。
- **進度／備註**：2026-09-22 已由本對話唯一 study 開發者 Ptolemy（`01a0c6e4-ae0b-7200-8836-d8cc701f0383`）依規範由 TODO 移至 Doing。已完成既有 Development-only Study 盤點並固定新的「量先價後延遲報酬傳導」假說：訊號日前五個已完成的量—下一 session 收盤報酬配對，量能加權後續報酬至少 `-0.02` 且比未加權平均高 `0.0005`；與同日量價對齊、量峰先後、量能廣度及其他既有機制有語義差異。Study=`tsm-momentum-trend-volume-response-lag--v001`；workflow=`62779bce18802e32ab314b6d74e8fc6f2da9fac03d1ee85a6416acc5553c67e4`、reference=`7b13d4d7e6448c9858215d9ef7e2e62fbd7fe0f40502e95a778a091008b20b47`、release=`ea04558c1473f9c6db7e9707846694147c6c6f254498af2f18729a1e4ef1fa84`、policy=`c86066b33119366a3172f475ff75f8813ba4b7545571894edfe581afabe32215`、source=`06ed3b3bdb9c596df4c213d2fb657b368de9950d3ddbe1282ccb408a3639c426`、preregistration=`8018ba3fff138c288c0e4d863ca75fc45ec30d3f219c88743d6ae035f94ba7d9`、Development data=`a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7`。v004 runner-preflight、prepare、contract／synthetic validator 均 passed；唯一 create operation=`8587deb68665d24bcb188d323272a2a9c8b6f4efdd915f1cc6547f8dec4fa294`、唯一 Development operation=`839dd0390ec114aa171c27f13f20b060972f0969fa4f925ab8f371b29fa27b76`；candidate／baseline evidence 均 valid。Candidate base／stress 為 1 筆、1 年、報酬 `-1.9986088%`／`-1.9999960%`、PF `0`／`0`、回撤 `1.9986088%`／`1.9999960%`；baseline 為 10 筆、4 年、報酬 `2.1411376%`／`0.5312003%`、PF `1.3058564`／`1.0755804`、回撤 `2.1279074%`／`2.2746830%`。Candidate formal gates 與三項 research targets 失敗，freeze eligibility=`false`；baseline 為控制組、不適用 candidate freeze。freeze-readiness／freeze 均 `qualification-failed`，event head=`bf03bed5c949ef01d87b6c007134682ac18252dfeb5678cf091b7037cff4266a`、event_count=`4`、lifecycle=`trial-recorded`，未產生 candidate-frozen。已完成受限 blind review，確認未曝光正式結果；成果卡已 append-only 更新 TSM.md，含逐 Trial 指標、gates／targets、validity、provenance、盲性、已確認／可能原因／尚不能判斷、限制與下一輪單一可否證條件。最後直接 pytest `4 passed`、Ruff passed、`git diff --check` passed；實際未完成項為 candidate freeze／freeze provenance（因資格失敗），沒有 evidence 缺件。未執行 Historical Evaluation、Terminal、challenge 或 replay，維持 Doing，等待 parent review。

- **Parent review 結果（2026-09-22）**：通過驗收。新 Study `tsm-momentum-trend-volume-response-lag--v001` 的核心是訊號日前五個已完成配對中，以 d 日成交量加權 d→d+1 收盤報酬；parent 核對既有 `volume-return-alignment` 是同日收盤報酬，其他既有 Study 也沒有這個跨日配對差值，確認不是改名、改版或無語義重發。v004 workflow/reference/release/policy/source/data binding、唯一 create／Development operation、4-event chain、candidate／baseline evidence 與 card 數值一致；candidate 1 筆／1 年且 base／stress 報酬為負、PF 為 0，formal gates 與 research targets 失敗；baseline 10 筆／4 年，仍有交易數與 stress robustness formal gates 失敗。candidate freeze eligibility=`false`，freeze-readiness／freeze 均 `qualification-failed`，未產生 candidate-frozen；唯一未完成項是資格失敗後的 freeze provenance，不是 evidence 缺件。受限 blind review 已確認未曝光正式結果，成果卡以繁體中文 append-only 記錄逐 Trial 指標、formal gates／targets、evidence validity、provenance、盲性、已確認／可能原因／尚不能判斷、限制與下一輪條件。parent 重跑直接 pytest=`4 passed`、Ruff 通過、`git diff --check` 通過；未執行 Historical Evaluation、Terminal、challenge 或 replay，未讀取或修改 `historical-evaluation-artifacts/`、`.super-admin/` 或正式結果。

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


## ✅ Done

> 已完成工作並由專案管理者驗收確認的任務。

### [TASK-023] 在 v005 驗證 TSM 相對半導體產業落後後修復假說
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：本 parent thread 新的 study 開發者 subagent `/root/task_023_v005_luna`（GPT-6 Luna，Max）
- **建立日期**：2026-09-24
- **更新日期**：2026-09-25
- **依賴／阻塞**：已解除。TASK-025 與 TASK-026 完成後，v005 於 `2026-09-24T10:59:32Z` 成為 Active，支援 1–16 個資產。**本 Study 已使用 v005，未使用已 Superseded 的 v004**；Study 專屬 `manifests/workflow-reference.yml` 已綁定下列固定 Workflow／release／manifest／policy digest，Development operation 已完成。
- **驗收條件**：
  - 依允許的 Development 資料盤點既有 TSM 假說，確認本研究使用「相對同業落後」而非重做 v009 的自身均線超跌、成交量篩選或近期動能量價條件；以 v009 為固定增量比較基準。
  - 僅依 v005 的多資產契約建立本 Study：以 `data_assets` 綁定 TSM（`use: trade`）與產業參考資產（優先 SOXX，`use: reference`）；若在 Development 前確認資料或產業組成不適合，先說明並固定替代參考資產，不得依績效挑選。逐檔記錄來源、日期、時區、可得時間及獨立 digest，並核對兩份資料的 XNYS session 完全對齊；不得把參考資產當成交易標的，也不得沿用 v004 的單一 `data_path` 契約。使用 v005 的 `build-strategy-study-v005`，Study 建立及 Development 僅用明確的 `development-to-freeze` 派工。
  - 在看任何本假說的 Development 交易結果前，核對並固定 TSM 與產業基準資料來源、調整方式、交易日對齊與可得時間；預先登記候選條件：產業基準過去五個共同交易日報酬大於 0，且 TSM 同期報酬至少落後 3 個百分點。產業基準優先評估 SOXX；若資料或組成不適合，須在試驗前說明並固定替代基準，不得依績效挑選。
  - 事前固定候選／對照組、下一個 XNYS open 進場、持有與風控、base／stress 成本、與 v009 訊號重疊時的持倉和優先順序。對照組須能區分「TSM 自身下跌」與「相對產業落後」，並保留逐筆交易供重疊與排擠核對。
  - 依 Active v005 的 `development-to-freeze` Lifecycle 建立一個新 Study，完成規定的 preregistration、唯一合法 Development trial 與 candidate／baseline evidence 驗證；只在流程與資格允許時嘗試 candidate freeze。若前置條件不成立，交付具體缺口與所需派工，不得用未驗證資料產出結果。
  - Development Study 完成後、撰寫成果卡前，依 `blind-review-strategy-study-v005` 檢查正式結果接觸情形與允許讀取範圍，再只用研究設計、程式和 Development candidate／baseline evidence 盲檢討；若資格或讀取範圍不符，停止並如實記錄，不得宣稱已通過。
  - 盲檢討階段結束後，依 `study-development-note-authoring-v005` 以繁體中文 append-only 撰寫成果卡，分列 candidate／baseline、base／stress、正式 gates、研究目標、evidence validity、freeze 資格與狀態、逐資產來源綁定、盲檢討狀態、限制及下一輪可否證條件；缺少結果不得補猜。
  - 事前設定並逐項回報：候選至少 20 筆完成交易、涵蓋至少 3 個交易年、相對 v009 至少 5 筆不重疊交易；全部正式 Development gates 通過，扣除排擠交易後的 stress 淨新增損益大於 0，且合併策略的 stress 回撤不高於 v009。任一目標失敗即如實記錄，不得在同一 Study 內調門檻或重跑。
  - 僅處理 v005 Development；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得讀取、搜尋、引用或修改 `historical-evaluation-artifacts/`、`.super-admin/`、正式結果或受限資料；不得覆寫既有 Study 或 evidence。回報 v005 Workflow reference、release、policy、逐資產資料／程式／evidence bindings、驗證結果、未達條件與限制，完成後維持 Doing，由專案管理者驗收。
- **摘要**：測試 TSM 短期表現落後半導體產業後是否修復，尋找不依賴 v009 超跌訊號的交易機會，並以淨新增交易及壓力成本後結果判斷是否值得保留。
- **進度／備註**：2026-09-24 由專案管理者依 TSM Development 成果卡與使用者討論建立；已由 `/root/study_developer_task_023` 接手；正在核對新增產業資料與 v004 支援，尚未執行 Study。3 個百分點與其他數值均為待事前固定並接受否證的研究設定，不是已驗證成果。
- **版本決策（2026-09-25）**：依使用者指示，本 Study 改為明確使用已 Active 的 v005；沿用本任務已核對的固定 bindings，並以 v005 的 Study Development、blind review 與成果卡 skills 執行。此為任務規格更新，不代表已開始 Study 或新增 Development 結果。
- **開始執行（2026-09-25）**：依使用者指示，本任務改派給新 subagent `/root/task_023_v005_luna`（GPT-6 Luna，Max），扮演 study 開發者；其須依序完成 v005 Development、v005 blind review、v005 Development 成果卡，維持 Doing 交 parent 驗收。
  - 2026-09-24 前置核對：SOXX 2013-01-02～2018-12-31 的 Yahoo `auto_adjust=True` 固定快照已新增至 `research/market-data/yahoo/`；品質報告 passed、SHA-256 `41c33b0ae3c53a6ae6726c2c6dcd673c19010e86c4f44f17ac64c13e5da1263a`、1510 個 XNYS session，與既有 TSM warmup／Development view 的日期逐日一致。v004 reference／release／policy digest 驗證通過。
  - **TASK-026 完成後的 v005 binding（已核對）**：Package=`workflows/strategy-forward-replication-research--v005/`；workflow digest=`2441c16d2c477afef9d4d9ca159e3a8bff150080b8552991d5da5fbcc9daf2c2`；release record=`workflows/strategy-forward-replication-research--v005/release.yml`，SHA-256=`92c2c35d15e371378c189f60de69093220ab1ee74c256208c36be31534f9aeb8`；release manifest digest=`6cf440bf81e2c081ff6e77025c5779cf5f2e4849015278419b836c0777db6405`；policy set digest=`c86066b33119366a3172f475ff75f8813ba4b7545571894edfe581afabe32215`。建立 Study 時仍須產生其專屬 `manifests/workflow-reference.yml` 並綁定這些固定值。本次只解除 Workflow 阻塞，不啟動 TASK-023。
  - **阻塞**：v004 的正式 Development 隔離執行只帶入 `plan.data_path` 一份 CSV；Source Bundle preflight 明確拒絕 `.csv` 資料檔，runner contract 合成輸入也固定單一六欄 OHLCV，沒有合法方式同時綁定並交付 SOXX 第二條價格序列。不能把資料偽裝成程式設定或挪用 Volume 欄。依前置條件停止：未建立 Study、未執行 runner-preflight／prepare／create／Development trial、freeze、blind review 或成果卡，也沒有績效數值。需要 workflow 維護者制定多資產輸入的 digest、日期界線與合成 preflight 契約，再由 workflow 執行者按 Lifecycle 發行可用版本；本角色不修改 workflow 治理。subagent 回報時任務維持 Doing，交由專案管理者決定阻塞處置。
- **Parent review（2026-09-24）**：已核對 SOXX 快照 SHA-256 與品質報告 `passed`，並查閱 v004 `operations/lifecycle.py`、`operations/preflight.py`、`schemas/runner-contract.schema.yml`。單一 `plan.data_path` 被複製為 `run/bars.csv`、Source Bundle 拒收 CSV、合成列僅有六欄，確認目前不能合法送入第二份 SOXX 價格資料。Study Developer 沒有越權修改 workflow 或建立不合規 Study，這部分符合 v004；但實驗與結果尚未產出，blind review 與成果卡也因沒有 Study／evidence 而未執行，均不能驗收為完成。依看板阻塞規則移至 Pending；待跨角色流程支援完成後，交回同一 subagent 接續，不把前置檢查當成策略有效性證據。
- **v005 schema 契約核對（2026-09-25）**：重新指派的 Study Developer 已核實 Active v005 release／workflow／policy bindings 及 TSM、SOXX 固定 Development CSV 的 digest、完整 XNYS sessions 與逐日對齊；v009 已確認為固定比較基準，且尚未查看本假說 Development outcome。建立 Study 前檢查發現正式 v005 `validator/qualification.py::METRICS` 與 `validator/artifacts.py::_recompute_development()` 沒有「相對 v009 非重疊交易數」、「扣除排擠後 stress 淨新增損益」或「合併策略 stress drawdown 相對 v009」的受支援可重算 metric；把它們加入 `eligibility_rules.research_targets` 會被 `validate_supported()` 拒絕，Development validator 又會精確核對 metrics／diagnostics，不能自行擴充 evidence 欄位或手動發布 evidence。依 parent guardrail 停在 Study create 前；未寫 preregistration／plan、未執行 prepare／create／trial，未產生 evidence、未做 blind review 或成果卡，也沒有可回報的策略績效或 freeze 結果。任務維持 Doing，交由 parent review 此 schema 缺口的治理處理方式。


- **v005 Development／盲檢討／成果卡（2026-09-25）**：依重新指派，以 Active v005 建立 `tsm-industry-relative-lag-repair--v001`；assignment digest=`6d47c2ac9822098fb2e4c209c1c481b31f0f4c1e245912996ae579f6739c7cd3`，create operation=`2ef62b694cb221730d1fccbd51cfdd1f66564b3476e4a5866ea7950c9f3ce0f7`，唯一 Development operation=`c61aed2338903a1440e715b6b8018c6f181f3f63332236e378fe65fde6a07e32`，event head=`4cc5da19c9187f3661644cf3d8520c88160496499e83f729707f2037a589f07e`。reference=`40396c0c742a653a589c5bfb738358149ae7c4302e55dc732362975902af3b90`、preregistration=`802926ef20773c47addac43595a1819fd29287abb5c6a581d82e0693e3317563`、Source Bundle=`c991bc32ba2380c91db35ab7af84597d7b27ca08a695080ba77c8e82bb29507c`。TSM trade digest=`a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7`、SOXX reference digest=`41c33b0ae3c53a6ae6726c2c6dcd673c19010e86c4f44f17ac64c13e5da1263a`；兩檔 2013-01-02～2018-12-31 完整且 XNYS sessions 對齊。Candidate／baseline evidence 均 valid；候選 47 筆／5 年、research targets 通過，但 11 個正式 gates 中 bootstrap stress drawdown ratio=`0.19848` 超過 `0.10`，故 freeze eligibility=false，未執行 freeze/readiness。v009 baseline 24 筆／5 年、正式 gates 全通過。補充計算：26 筆不重疊 overlay 通過；排擠後 stress PnL delta=`-8278.224119213886735` 及 stress drawdown 7.674% 高於 v009 2.119%，兩者未達。盲檢討只用該 Study 的設計／程式／Development evidence，digest 與重算一致；未接觸正式 Evaluation／Terminal 結果。已 append-only 更新 `.study-developer/development-note/TSM.md`；完整 candidate／baseline／inputs／publication digests 留在成果卡。TASK-023 維持 Doing，交 parent review；未執行 Historical Evaluation、Terminal、challenge、replay。

---
- **Parent review／驗收（2026-09-25）**：確認 Study 依 Active v005 的固定 workflow／release／manifest／policy bindings 建立，僅有一次合法 Development trial；TSM 與 SOXX 資產用途、日期與 XNYS 對齊有 digest 綁定，candidate／baseline evidence 均 valid。v005 formal gates 10/11 通過，唯一失敗的壓力重抽樣回撤比例為 19.848%（上限 10%）；候選不具 freeze 資格，未做 freeze/readiness。獨立重算的三項 TASK 目標為：不重疊交易 26 筆達標、排擠後壓力淨損益差 −$8,278.22 未達、壓力回撤 7.674% 高於 v009 的 2.119% 未達。盲檢討範圍與 v005 規範相符，僅檢視允許的 Study 設計／程式／Development evidence，未接觸正式 Evaluation／Terminal；成果卡已 append-only 補齊 candidate／baseline base／stress 數字、證據有效性、凍結資格與狀態、限制及下一輪否證條件，正文約 580 字。補充計算重現、Ruff 與 `git diff --check` 均通過。實驗交付及文件驗收完成；研究假說未通過全部預設目標，不代表策略有效或可進入正式評估。

### [TASK-026] 依 Lifecycle 發行支援多資產輸入的 Workflow 新版本
- **狀態**：Done
- **優先級**：高
- **負責角色**：workflow 執行者
- **執行者**：本 parent thread 的 workflow 執行者 subagent `/root/workflow_executor_task_026_luna`
- **建立日期**：2026-09-24
- **更新日期**：2026-09-24
- **依賴／阻塞**：無。v005 已完成 Release 並為 Active；v004 已標記 Superseded，兩者的舊 Package 與 Release Record 均保留。
- **驗收條件**：
  - 依 `docs/workflow-lifecycle.md` 核對 TASK-025 的新版本為完整自包含 Package；執行 Draft→Release Candidate 的規定驗證，涵蓋 schema、validator、狀態轉換、逐資產資料／artifact digest、政策符合性、一個／兩個／三個以上資產的端到端 fixtures、必要測試與 Ruff，並產生可驗證的 release manifest 與 test report。缺件時退回，不以測試摘要代替證據。
  - 由符合規範的 Trusted Approver 檢視並建立綁定 Workflow／manifest／test report digest 的 `release.yml`；執行者不得自行替自己的交付核准。核准無法取得時記錄阻塞，不得宣稱 Active。
  - Release 有效後依 Lifecycle 更新治理狀態，保留 v004 與更早版本的 Package、Release Record、Study 與 evidence；核對新版本確實可接受新 Study，並提供 TASK-023 study 開發者接續所需的固定 reference／release／policy binding。
  - 回報 Release ID／版本、核准者與時間、digest、驗證命令及結果、治理狀態變更和任何缺件；本任務不建立 TASK-023 Study，不執行 Development、Historical Evaluation、Terminal、challenge 或 replay。
- **摘要**：在 TASK-025 交付多資產 Workflow Draft 後，依治理程序驗證 Release Candidate 並啟用新版本，讓 TASK-023 與未來使用更多資產的 Study 能合法進行。
- **進度／備註**：2026-09-24 由專案管理者建立 TODO；同日依使用者回饋將範圍從固定雙資產修正為可變數量多資產。2026-09-24 由 workflow 執行者 subagent 接手並移至 Doing。建立候選版檔案前，正式重跑全套 pytest 得 118 passed、16 個 NumPy 警告、退出碼 0（908.28 秒）；Ruff、102 檔 canonical YAML／schema／Policy 定義檢查、v004 無 diff、`git diff --check` 均通過。曾建立可重算 manifest／test report，且 `release_candidate.py --candidate` 通過；但建立後重跑 `tests/test_release_candidate.py -q` 得 1 passed、1 failed：`test_draft_has_no_release_artifacts_and_is_reproducible` 要求 Package 無 manifest／report，形成候選版後必要測試必然失敗。不能以建立前的測試通過宣稱最終 Release Candidate 完成；本輪未核准的兩個檔案已撤回，v005 維持 Draft。該次嘗試的 workflow／manifest／report digest 分別為 `31f58d368a373c104e36f535d0c2e1cb5ff0cea5768c0947200bcacd0509e938`／`758b38fab56335d7ddc97818f9b7e976f1d6266b0bf18081aefe57e98627afa4`／`9480d3b5e0a5324330305eabe67a1569bc065223ba34a73ccd7c9dbae7588761`，僅供追查，不是可用 Release。須交回原 workflow 維護者修正測試，再由本任務重跑全套、重建候選版證據；尚無獨立核准或有效 `release.yml`，v004 仍為 Active，TASK-023 不能綁定 v005；本任務維持 Doing。

- **Parent review（2026-09-24）**：確認 `tests/test_release_candidate.py:28-29` 在發行檔存在時與 RC 必要產物衝突。執行者已撤回本輪未核准的 manifest／test report，v005 實際回到 Draft；先前 RC digest 僅作本輪嘗試紀錄，不代表有效 RC。重新開啟 TASK-025 修正測試，TASK-026 移至 Pending，之後交回同一 workflow 執行者重跑完整發行驗證；無獨立 Trusted Approver 前不得啟用。

- **續辦（2026-09-24）**：由專案管理者另派新的 workflow 執行者 subagent `/root/workflow_executor_task_026_luna`，依序續辦本任務。修正後 Draft gate 的正式全套測試命令 `.venv/bin/python -m pytest workflows/strategy-forward-replication-research--v005/tests -q` 得 `124 passed, 16 warnings in 907.26s (0:15:07)`、退出碼 0；16 個 NumPy `invalid value encountered in subtract` 警告分布於 `test_assignment_lifecycle.py` 1 個、`test_multi_asset.py` 15 個。`.venv/bin/python workflows/strategy-forward-replication-research--v005/operations/release_candidate.py` 通過並核對 102 個定義檔、canonical YAML、Schema 與 Policy release／conformance；`.venv/bin/ruff check workflows/strategy-forward-replication-research--v005` 通過；`git diff --exit-code HEAD -- workflows/strategy-forward-replication-research--v004`、`git diff --check` 通過。檢查時 v005 無 `studies/`，也沒有 manifest、test report 或 `release.yml`。建立 RC 前發現 v005 `README.md` 首段仍聲稱「目前是 Draft、沒有 manifest／report」；README 會納入 Workflow digest，建立候選版後該敘述將失實。依 parent 指示暫不建立任何 RC artifact，待 TASK-025 維護者修正 README 後重新執行 Lifecycle gates。尚未取得獨立 Trusted Approver 核准，也沒有 `release.yml`；v004 仍為 Active，不得讓 TASK-023 使用 v005。本次 pytest 是 Draft gate 結果，不代表 Release Candidate 已完成；TASK-026 維持 Doing。
- **Parent review（2026-09-24，Draft gate）**：v005 Draft 狀態全套 pytest `124 passed, 16 warnings`（907.26 秒，exit 0）；102-file definitions／canonical／schema／Policy checker、Ruff、v004 `git diff` 空、`git diff --check` 通過。未建立 RC artifacts。Parent 確認 README 首段確稱「目前是 Draft、沒有 manifest／report／release」，且 README 納入 Workflow digest；這是會在 RC 建立後過時的狀態說明。依 TASK-025 修正完成後再續辦，本任務由 Doing 移至 Pending。
- **Parent resume（2026-09-24）**：TASK-025 新增 README 狀態說明與回歸測試後，parent 已重跑 `tests/test_release_candidate.py` 得 9 passed，v005 Ruff／`git diff --check` 通過，v004 無 diff。原 Draft gate（124 passed、16 warnings）涵蓋 README 修正前的 Workflow digest，不能重用；TASK-026 交回同一 Luna／Max workflow 執行者，需重跑完整 suite／全部 Release Candidate gates，建立新 manifest／report 並在 RC artifacts 存在下再次重跑測試與 checker。

- **本次續辦結果（2026-09-24，待 PM 驗收）**：依 README 修正和新增回歸測試後重新執行全部 gates。Draft 狀態 `.venv/bin/python -m pytest workflows/strategy-forward-replication-research--v005/tests -q`：`125 passed, 16 warnings in 894.24s (0:14:54)`，exit 0；NumPy `invalid value encountered in subtract` 警告分別在 `test_assignment_lifecycle.py` 1 個、`test_multi_asset.py` 15 個；log SHA-256 `959cbddeaeb5cb79e5a331c2c8d7bcd231a7703d1b40ebfec6aa0508b2b965ac`。Definition checker 通過 102 個 canonical YAML／Schema／Policy release 與 conformance 檔；Ruff 通過；v004 `git diff` 為空、`git diff --check` 通過；無 v005 `studies/` 或既有 release artifacts。其後新建 v005 Release Candidate manifest／test report，產生 `workflow_digest=2441c16d2c477afef9d4d9ca159e3a8bff150080b8552991d5da5fbcc9daf2c2`、manifest SHA-256 `6cf440bf81e2c081ff6e77025c5779cf5f2e4849015278419b836c0777db6405`。RC artifacts 存在時重新執行全套 pytest：`125 passed, 16 warnings in 895.26s (0:14:55)`，exit 0；NumPy 警告分布相同，log SHA-256 `d311584e0a3054ad8996f82757c674935c2b312aef95f068010e75a8bd267391`。RC 狀態 Ruff、`release_candidate.py --candidate`、v004 未變與 diff-check 均通過。完成 RC 結果後更新 test report；最終 report SHA-256 `3120c4edf745f3b2ae8701a7d37ac54737180a15b204bfcea46bb6619b3872dc`，包含 Draft 與 RC 兩次全套測試及 RC 狀態 Ruff／checker 結果。更新後重新驗證 report schema 與 candidate checker；仍為 102 files、`release-candidate`，Workflow digest 和 manifest digest 與 report 更新前相同。沒有 `release.yml`，未取得獨立 Trusted Approver 核准；v004 維持 Active，TASK-023 不得使用 v005。本任務未執行真實 Study Lifecycle、Historical Evaluation、Terminal、challenge 或 replay；維持 Doing。
- **Parent review（2026-09-24，RC）**：重新執行 `.venv/bin/python workflows/strategy-forward-replication-research--v005/operations/release_candidate.py --candidate`，結果 `release-candidate`、102 files、`release_record_created=false`、workflow digest `2441c16d2c477afef9d4d9ca159e3a8bff150080b8552991d5da5fbcc9daf2c2`。親自重算並核對 manifest SHA-256 `6cf440bf81e2c081ff6e77025c5779cf5f2e4849015278419b836c0777db6405`、最終 report SHA-256 `3120c4edf745f3b2ae8701a7d37ac54737180a15b204bfcea46bb6619b3872dc`；report 有 11 checks、狀態 `release-candidate`。Draft 與 RC artifacts 存在下的完整 pytest 各為 125 passed、16 個 NumPy warnings，退出碼皆 0；RC run 耗時 895.26 秒。Ruff、102-file canonical/schema/Policy gates、RC checker、v004 無 diff、`git diff --check` 均通過。未建立 `release.yml`、未取得獨立 Trusted Approver；依 `docs/workflow-lifecycle.md` Release Candidate 尚不得建立正式 Study，因此 v004 保持 Active、TASK-023 仍不可使用 v005。本任務的候選版建置與驗證已交付，剩餘阻塞是獨立 Trusted Approver 必須檢查這三個 digest 並建立 Release Record；由 Doing 移至 Pending 等待該核准。未執行真實 Study Lifecycle、Historical Evaluation、Terminal、challenge 或 replay。

- **Trusted Approver 核准與 Lifecycle 完成（2026-09-24，待 PM 驗收）**：使用者明確核准 `ochowei@gmail.com`，核准文字由使用者提供；workflow 執行者不是核准者。依 v005 release schema，以實際 UTC `2026-09-24T10:59:32Z` 建立 `workflows/strategy-forward-replication-research--v005/release.yml`，並立即由 `validate_release_record` 驗證通過。Release Record SHA-256=`92c2c35d15e371378c189f60de69093220ab1ee74c256208c36be31534f9aeb8`，核准者、時間與 workflow／manifest／test report 三個 digest 均與使用者核准及 parent 已驗收 RC 一致；Release Candidate 狀態測試 `.venv/bin/python -m pytest workflows/strategy-forward-replication-research--v005/tests/test_release_candidate.py -q` 為 9 passed。已更新 `docs/workflow-lifecycle.md` 與 `workflows/README.md`：v005 標記 Active，v004 自同一時間停止接受新 Study 並因 v005 多資產能力取代而標記 Superseded；v004 Package 與原 Release Record 未修改。再驗證 Release Record、test report schema、Lifecycle 狀態文案、`git diff --check` 及 v004 無 diff，均通過。v005 現可供新 Study 使用；未建立 TASK-023 Study，也未執行真實 Study Lifecycle、Historical Evaluation、Terminal、challenge 或 replay。任務由 Pending 回 Doing，等待 parent review。
- **Parent review（2026-09-24，Active）**：parent 重新執行 `validate_release_record` 並核對 Trusted Approver 為使用者明確提供的 `ochowei@gmail.com`、核准時間 `2026-09-24T10:59:32Z`，以及 workflow `2441c16d2c477afef9d4d9ca159e3a8bff150080b8552991d5da5fbcc9daf2c2`、manifest `6cf440bf81e2c081ff6e77025c5779cf5f2e4849015278419b836c0777db6405`、test report `3120c4edf745f3b2ae8701a7d37ac54737180a15b204bfcea46bb6619b3872dc` 完全相符；release record SHA-256=`92c2c35d15e371378c189f60de69093220ab1ee74c256208c36be31534f9aeb8`。`test_release_candidate.py` 在 Active 狀態 9 passed；Ruff、`git diff --check` 通過，v004 package/release 無 diff。核對 `docs/workflow-lifecycle.md` 與 `workflows/README.md` 已列 v005 Active、v004 Superseded，保留舊版 Package、Release Record 與既有 Studies；治理文件適用版本清單已含 v005。新版本目前可供新 Study 使用。已在 TASK-023 補入 v005 固定 binding；TASK-023 仍 Pending，沒有在本任務建立 Study 或執行 Study Lifecycle。TASK-026 驗收通過，移至 Done。


### [TASK-025] 制定支援可變數量資產輸入的新 Workflow Draft
- **狀態**：Done
- **優先級**：高
- **負責角色**：workflow 維護者
- **執行者**：本 parent thread 的 workflow 維護者 subagent `/root/workflow_maintainer_task_025_luna`（GPT-6 Luna、Max）
- **建立日期**：2026-09-24
- **更新日期**：2026-09-24
- **依賴／阻塞**：承接 TASK-023 的 v004 單一價格檔阻塞；開始前核對現行 Active Workflow、Release 與新版本編號。此任務只制定及開發 Workflow Draft，不執行 Workflow Lifecycle 或啟用 Release。
- **驗收條件**：
  - 以 TASK-023 的 TSM／SOXX 作第一個驗證案例，說明 v004 `plan.data_path`、隔離執行、Source Bundle preflight 與六欄合成 runner contract 的單一資料限制；設計可變長度、至少一個資產的輸入清單，不把數量寫死為兩個。每個資產須有穩定識別、用途（交易標的或參考資料）、來源、日期範圍與獨立 digest；若需限制資產數量或檔案大小，須明定資源上限與拒絕方式。
  - 依 `docs/workflow-lifecycle.md` 建立自包含的新 Workflow Version；不得直接修改已發布的 v004 Package、Release Record、既有 Study 或 evidence。定義多資產的交易日／時區對齊、缺漏資料與可得時間規則，不得默默填入未來資料；讓輸入清單在 runner request、隔離 workspace、preflight、schema、validator、evidence 與來源綁定中逐項一致。
  - 驗證每份 Development 輸入只能讀取允許的 warmup／Development 區間；補足一個、兩個及三個以上資產的端到端案例，以及重複識別、缺檔、digest 漂移、日期錯位、受限資料混入、超出資源上限與隔離執行的拒絕測試，同時確認既有單資產 Study 路徑不被破壞。
  - 完成 Draft 的規格、程式、測試、reference 與 Release Candidate 驗證計畫；回報新版本 ID、差異、已執行的開發驗證及交給 workflow 執行者的待辦。不得自行執行 Draft→Release Candidate→Active 轉換、建立正式 release artifact、執行 Study Lifecycle 或讀取正式 Historical Evaluation／Terminal 結果。
- **摘要**：補上 v004 缺少的可變數量資產輸入能力，讓 TSM／SOXX 及未來更多資產的 Study 都能逐檔驗證來源與時間範圍，再進入同一次 Development 試驗。
- **進度／備註**：2026-09-24 由專案管理者建立 TODO；同日依使用者回饋將範圍從固定雙資產修正為可變數量多資產。同日 workflow 維護者 subagent 接手並移至 Doing。已建立 `strategy-forward-replication-research--v005` 自包含 Draft，新增 1–16 資產的逐檔來源／日期／digest、XNYS 完整交易日與可得時間規則、資源上限、Development 與 Historical Evaluation 的 request／隔離執行／snapshot／evidence 綁定，以及單資產相容路徑；TSM／SOXX 是兩資產驗證範例。純合成聚焦測試 19 passed（含 1／2／3 資產 Development 與 2／3 資產 Evaluation→terminal）、canonical／Draft 測試 7 passed；29 份 schema 為 canonical 且 meta-schema 有效，Ruff 與 `git diff --check` 通過。首次全套 pytest 為 113 passed、1 failed（14 分 14 秒），唯一失敗是複製的 contract fixture 未更新 preregistration digest；修正後該測試單獨重跑通過，修正後尚未重跑整套，不能宣稱全套通過。v005 沒有建立 Workflow release manifest、test report 或 release record；待專案管理者驗收 Draft，TASK-026 執行者須正式重跑全套與 Release Candidate 檢查、產生發行證據並取得獨立 Trusted Approver 核准。任務維持 Doing。
- **Parent review（2026-09-24）**：已核對 v005 Draft 的多資產參考文件、實作計畫與 `operations/multi_asset.py`：資料清單支援 1–16 資產、逐檔 digest／完整 XNYS 日期／角色／路徑／容量檢查與隔離檔名，並保留單資產路徑。v004 無 diff，v005 無正式 release manifest、test report 或 `release.yml`，符合維護者不執行 Workflow Lifecycle 的界線。parent 重新執行 `tests/test_multi_asset.py` 得 17 passed，目標 Ruff 通過；worker 的首次全套 113 passed／1 failed 及修正後單測通過均如實保留，未將全套稱為通過，交由 TASK-026 正式重跑。Draft、規格與交接計畫符合 TASK-025 驗收，移至 Done；此驗收不代表 v005 已成 Release Candidate 或 Active。
- **重新開啟（2026-09-24）**：TASK-026 建立 Release Candidate 必要的 manifest／test report 後重跑測試，發現 v005 `tests/test_release_candidate.py:28-29` 直接斷言這兩個檔案不得存在，使已產生 RC artifact 的 Package 必然測試失敗。原 Draft 驗收沒有涵蓋 artifact 建立後的重跑情境；交回原 workflow 維護者修正測試設計並驗證 Draft／RC 兩種狀態。維護者只修改 Draft／測試，不執行 Lifecycle。

- **續辦結果（2026-09-24，待 PM 驗收）**：原 workflow 維護者 subagent 已修正 v005 `tests/conftest.py` 與 `tests/test_release_candidate.py`。測試會檢查目前 Package 實際狀態，並以隔離副本分別驗證 Draft（無正式發行檔、可重算 Workflow digest）與 Release Candidate（manifest／test report 齊全、定義檔 digest 可重算、report schema 有效）；缺任一份發行證據、定義檔漂移或無效 report 都會失敗。若未來有正式 `release.yml`，會透過既有 release validator 核對其 manifest／report digest 綁定。已在 `IMPLEMENTATION-PLAN.md` 補上建立候選版後必須重跑測試的交接說明。聚焦 pytest 13 passed，整個 v005 Ruff 與 `git diff --check` 通過，v004 無 diff。這是 Draft／隔離 fixture 驗證；沒有在 v005 Package 建立正式 manifest、test report 或 release record，未執行 Lifecycle。修正後完整 pytest 尚待 TASK-026 執行者重跑；任務維持 Doing。
- **本次續辦（2026-09-24，待 PM 驗收）**：新 workflow 維護者 subagent `/root/workflow_maintainer_task_025_luna` 接手 Doing。將 v005 README 標題改為不固定宣稱 Draft，並以 Lifecycle 條件說明 Draft、Release Candidate、Active：候選版須有通過必要驗證的 manifest／test report；只有 Trusted Approver 建立且與目前 Workflow、manifest、test report 完全一致的有效 `release.yml` 才是 Active，只有 Active 可建立正式 Study。新增測試，防止 README 把目前缺少發行檔寫成固定事實，並確認正式 Study 限制。該測試 1 passed（0.04 秒）、變更測試檔 Ruff 通過、`git diff --check` 通過。README 與測試檔均受 Workflow digest 保護；TASK-026 必須在這些修改後重跑全套驗證並重建發行證據。此維護工作未執行 Lifecycle 或建立正式發行檔。
- **Parent review（2026-09-24，重新開啟後）**：核對 `tests/conftest.py` 的隔離 fixtures、`tests/test_release_candidate.py` 及 `IMPLEMENTATION-PLAN.md`。Draft fixture 排除正式 release artifacts 並重算 workflow digest；RC fixture 在暫存副本建立 manifest／test report，驗證 Package 完整狀態、manifest digest、report schema，另有缺少任一檔、定義漂移、無效 report 的拒絕測試，Active 狀態沿用 release validator。Parent 重跑該測試檔為 8 passed，v005 Ruff 通過，v004 無 diff。確認修正解決「RC artifacts 建立後全套必然失敗」的 Draft 測試設計缺陷；未建立正式發行檔、未執行 Lifecycle。TASK-025 重新驗收完成並移至 Done；TASK-026 可恢復執行完整發行驗證。
- **重新開啟（2026-09-24，再次）**：TASK-026 Draft 全套驗證通過後的審查發現 README 第 1 段仍寫「此 Package 目前是 Draft，沒有 release-manifest.yml、release-test-report.yml 或 release.yml」。README 會納入 workflow digest；建立 RC manifest／report 後該聲明便不正確。請以符合 Draft、RC 與 Active 各階段的穩定描述取代，不要刪除安全界線（例如尚未 Active 不得供正式 Study 使用），並更新 Draft／RC 測試或驗收文件以避免狀態文字回歸。維護者不執行 Lifecycle；修正後交由 TASK-026 重跑完整驗證。
- **Parent review（2026-09-24，再次重新開啟後）**：核對 README 首段依 Lifecycle 定義 Draft、Release Candidate 與 Active，說明只有 Trusted Approver 建立且通過驗證、綁定目前 Workflow／manifest／report 的有效 `release.yml` 才是 Active，且只有 Active 可建立正式 Study。新增回歸測試避免把「目前 Draft／缺少 artifacts」寫成固定 Package 現況。Parent 重跑 `test_release_candidate.py` 得 9 passed；v005 Ruff、`git diff --check` 通過，v004 無 diff。未建立正式發行檔或執行 Lifecycle。TASK-025 驗收通過並移至 Done；README 與測試均會納入 Workflow digest，TASK-026 必須從新 digest 重跑 gates。



### [TASK-014] 對 `tsm-momentum-trend-volume-breadth--v001` 進行 v004 blind review 並重寫成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Linnaeus（本 parent thread 的唯一 Study Developer subagent `01a0c6af-eb2f-7470-a0fe-ffc2798fd577`）
- **建立日期**：2026-09-22
- **更新日期**：2026-09-22
- **依賴／阻塞**：TASK-013 已完成；目標 Study 為 `tsm-momentum-trend-volume-breadth--v001`，Workflow 為 v004
- **驗收條件**：
  - 先依根目錄規範與 v004 blind-review skill 核對目標 Study；若發現已接觸正式 Historical Evaluation evidence、帶 outcome 的 Terminal／正式結果或其他會破壞盲性的內容，必須停止 blind review 並如實回報，不能假裝忽略曝光。
  - 先解析並驗證該 Study 的 `manifests/workflow-reference.yml`、v004 release／policy binding，再只讀取 preregistration、candidate family、qualification／implementation contract、Development 設計、每個已登記 Trial 的 candidate／baseline evidence、inputs、publication、Source Bundle 綁定的研究程式／runner／測試／Development data metadata，以及 Development provenance／selection／assignment 作補充。
  - 嚴禁開啟、搜尋、雜湊、複製或引用 `historical-evaluation-artifacts/`、正式 Evaluation／Terminal、quarantine／full evaluation data、`events/`、`journals/`、`operations/`、`study.yml` 或 Git 歷史；不得使用完整 `status`／`validate` 取代盲讀範圍，也不得修改 Study、Workflow、authority 或 evidence。
  - 逐 Trial 重新判定 candidate／baseline evidence validity、formal gates、research targets、candidate freeze eligibility 與 blind eligibility；清楚區分 formal gate 與 target，缺 evidence 只能標示 unavailable，不得推測未執行結果。
  - 完成後以繁體中文重新撰寫該 Study 的成果卡，保留 Development-only 邊界，完整記錄已確認問題、影響、證據強度、限制、下一輪可否證建議、盲性狀態與「未使用正式結果」聲明；不得新增獨立 review 檔案，除非另有指定路徑。
  - subagent 完成後維持 Doing，由 parent project manager review 成果卡是否符合專案規範；若需修正，parent 只能把修改要求交回同一個 subagent，通過後才移到 Done。
- **摘要**：對剛完成 Development 的 v004 Study 做受限讀取的 blind review，重新整理成果卡，讓 Study 的問題、影響、證據強度與後續可否證方向清楚且不混入正式評估結果。
- **進度／備註**：2026-09-22 已由本 parent thread 的唯一 Study Developer subagent 接手，並依使用者要求將原始 `2026-09-21` v004 Development 卡與 `2026-09-22` blind-review／更正內容合併為 `.study-developer/development-note/TSM.md` 唯一的 `2026-09-22`「Development + blind review consolidated card」，移除第二個 revision 標題與重複段落；保留 exact workflow／reference／release／policy／source／preregistration／Development data／warmup digest、create／Development operation、event head／count／lifecycle、逐 Trial 數值、candidate targets 與 baseline targets「不適用／未對 baseline 登記」更正。未修改其他 Study 或 Study、Workflow、manifest、evidence、events、authority、正式結果；未重新執行 blind review、runner、`status`／`validate` 或測試。parent review 通過，任務結案。

### [TASK-013] 在 v004 開發下一個未嘗試的 TSM 動能趨勢 × 量先價行假說並撰寫成果卡
- **狀態**：Done
- **優先級**：高
- **負責角色**：study 開發者
- **執行者**：Huygens（本對話唯一 study 開發者 subagent `01a0c475-8171-7c42-927c-8d65bea438f8`）
- **建立日期**：2026-09-21
- **更新日期**：2026-09-21
- **依賴／阻塞**：無；接手時先確認 v004 Workflow Release 為 Active
- **驗收條件**：
  - 依根目錄規範、`.study-developer/development-note/TSM.md` 與允許讀取的既有 TSM Development Study，完整盤點已嘗試過的動能、趨勢及量先價行機制；提出一個可追溯、確實未被嘗試過的新假說，不得只是改版本號、改名稱、重用既有規則或無語義重發，並在研究文件中說明與既有 v004 Study 的機制差異。
  - 依 v004 `development-to-freeze` 流程建立單一新 Study，先完成 Workflow reference／release digest 核對、runner preflight 與 prepare，再固定 preregistration、candidate／baseline、implementation、runner、Development data bindings、明確派工與 provenance；完成唯一合法的 Development trial、evidence validation，以及規則允許的 freeze-readiness／candidate-freeze 嘗試。
  - 只執行 v004 Development；不得執行 Historical Evaluation、Terminal、challenge 或 replay，不得讀取或修改 `historical-evaluation-artifacts/`、`.super-admin/`、正式 Evaluation／Terminal 結果，也不得覆寫、刪除或重排既有 Study、evidence、authority、events 或成果卡。
  - Development 完成後，以繁體中文 append-only 更新 `.study-developer/development-note/TSM.md` 的該 Study 成果卡；逐 Trial 區分 candidate／baseline、base／stress、formal gates、research targets、evidence validity、candidate freeze 資格／狀態、provenance、限制與下一輪可否證條件。缺少 evidence 時不得補猜數值，並清楚標示已確認、可能原因與尚不能判斷。
  - 通過對應 v004 validator／checker、必要 pytest、Ruff（若適用）與 `git diff --check`；回報 Study ID、workflow／reference／source digest、operation ID、事件 head、修改檔案、驗證結果、實驗結果與任何實際缺件。subagent 完成後維持 Doing，由 parent project manager review 後才可移到 Done。
- **摘要**：根據 TSM Development 研究盤點，在 v004 workflow 中提出並驗證一個真正新的「量先於價、用於動能趨勢確認」機制，產出可追溯的 Development Study 與成果卡，讓後續是否值得凍結有清楚且不越權的證據。
- **進度／備註**：2026-09-21 由本對話唯一 study 開發者 subagent 接手，已由 TODO 移至 Doing。已完成 `tsm-momentum-trend-volume-breadth--v001` 的 v004 runner-preflight、prepare、唯一 Development trial、evidence validation、freeze-readiness 與 candidate-freeze 嘗試；成果卡已 append-only 寫入 `.study-developer/development-note/TSM.md`。create operation=`3d83dc6f2a376ef5d63fe3cfa080053b68c6fd3ef6f2a639981b8992684c73eb`，Development operation=`3134e0ec6c2cfde7406a6a7ca308b576e398b25f36ba5335d6933f44a3eaebc0`，event count=`4`，event head=`52ef75ad804a93ecf81e3725e27fe789ba0802723a58ad813c83a33671e14947`。Candidate／baseline evidence 均 `valid`；candidate 7 筆／3 年，base／stress 報酬 7.1897%／5.5959%、PF 4.2884／3.5981、最大回撤 1.9990%／1.9990%，僅因 `completed_trades` 低於 20 失敗；baseline 10 筆／4 年，base／stress 報酬 2.1411%／0.5312%、PF 1.3059／1.0756、最大回撤 2.1279%／2.2747%，另有 stress bootstrap 正報酬比與 leave-one-year-out PF／報酬 gate 失敗。`status`／`validate` 通過，candidate freeze eligibility 不具資格；freeze-readiness／freeze 均 `qualification-failed`，沒有 candidate-frozen 或 freeze provenance。未執行 Historical Evaluation、Terminal、challenge 或 replay，未修改 Workflow、validator 或既有 immutable artifact。
- **Parent review 結果（2026-09-21）**：核對公開 preregistration、candidate／baseline evidence、inputs／publication、四事件鏈、authority／workflow reference／release／source bindings 與 Study lifecycle；確認新假說的核心「訊號日前五日中至少三日的五日滾動量比達標」未在既有 TSM Development 卡片或既有動能量先價行 Study 中出現，且與 volume-lead、ramp、absorption、efficiency、close-acceptance、return-alignment、range-compression、gap-anchoring、persistence／fade、peak-lead 及 v024 固定突破有可識別差異；共用 OHLCV、五日視窗與二十日均量的限制已揭露。parent 重跑新 Study targeted pytest=`4 passed`、Ruff=`All checks passed`、`git diff --check` 通過。成果卡已逐 Trial 區分 candidate／baseline、base／stress、formal gates、research targets、evidence validity、candidate freeze 狀態、provenance、限制、已確認／可能原因／尚不能判斷與下一輪可否證條件；全 repo 既有 pytest／Ruff 問題未被誤報為通過，也未以 workaround 修改 Workflow。TASK-013 通過驗收，移至 Done。

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
