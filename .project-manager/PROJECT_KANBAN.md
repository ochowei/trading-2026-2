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

（目前沒有 Pending 任務）

---

## ✅ Done

> 已完成工作並由專案管理者驗收確認的任務。

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
