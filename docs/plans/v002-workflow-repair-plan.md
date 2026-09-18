# v002 修復與 Skill／CLI 整合計畫

本計畫針對提交 `4372f6b` 的 Release Candidate，修復 review 已重現的四個缺漏，並讓後續 Study 可以由 skill 配合 CLI 完成。這是實作計畫，不是核准、任務分派或已完成的驗收紀錄。

## 1. 目標與交付邊界

修復後，操作者只需提供研究設計、必要核准與 provenance（資料來源及曾接觸哪些結果的事實），不需要手動拆 evidence、補 digest、拼接事件或清除鎖檔。CLI 必須能說明目前完成到哪一步、為何不能往下走，以及如何安全接續。

研究目的、資料切割、事件種類及結果權限維持不變；本次調整 CLI 的組合操作，不合併底層事件、不宣稱跨事件原子性。若實作發現必須改變狀態模型，另提治理議案，不自行變更。

v002 尚未 Active，可修正同一 Draft Package 後重新形成 RC。開始修改後，原 RC 報告不再代表新內容；保留原提交可追查，完成全部驗證後重新產生 manifest 與測試報告。修復與測試只用隔離 fixtures，不執行真實 Study 或正式 Historical Evaluation，不建立正式 `release.yml`，也不改動 v001、既有 Study 或已引用 Policy。

## 2. 三層責任：重要保證不能只寫在 skill

| 層級 | 必須負責 | 不應負責 |
| --- | --- | --- |
| Workflow validator／writer | 從 raw evidence 重算、候選資格、佐證完整性、事件轉換、內容綁定、不可覆寫與恢復 | 信任 skill／caller 自報的 pass、eligible、clean |
| CLI | 組裝固定輸入、呼叫正式 runner、發布證據、串接既有事件、回報下一步 | 自動產生人員核准、替研究者補造 provenance、變更 frozen inputs |
| Skill | 釐清假說、協助準備規格、取得缺少的事實或核准、呼叫 CLI、解釋結果及交接 | 手工拆 evidence、重寫另一套 eligibility 判斷、繞過 CLI、猜測 authority root |

所有高階命令共用同一組服務函式；低階 writer、獨立 validate 與 recover 也必須落實相同不變條件。Skill 是使用方法，不是資料權限隔離或核准身分的技術證明。

## 3. 預期的日常流程

以下名稱是建議介面，實作時固定於 v002 的 `operations/cli.py`；不先修改共用 v001 `studyctl` 的預設行為。

```text
Skill 協助建立研究 bundle 與既有核准依據
  → prepare
  → create-authorize
  → development
  → freeze
  → 停在 candidate-frozen，交接給 Evaluation 角色
```

| 命令 | 操作者提供 | CLI 自動完成 |
| --- | --- | --- |
| `prepare <id>` | 研究 bundle、runner contract、合成案例 | 新 ID／authority、規格、source、contract、完整 runner 與正式證據消費路徑的隔離驗證，產生有指紋的報告 |
| `create-authorize <id> --plan …` | 綁定該研究及規格的既有核准依據 | 重驗 prepare；依序發布 study-created、preregistration-approved、development-authorized；保存可接續的操作紀錄 |
| `development <id> --trial …` | 預先登記的 trial 與資料 reference | 以 frozen runner 執行、保存及驗證輸出、發布 candidate／baseline 證據、追加 trial-recorded；績效不合格仍保留有效證據 |
| `freeze <id> --plan …` | 真實 provenance 佐證、所需核准；候選集合已完整 | 先執行完整 freeze-readiness，再依既有順序發布 registry、provenance、candidate freeze；不合格就說明原因，不補造候選 |

`freeze` 可組合 trial-registry-frozen、provenance-audited、candidate-frozen，但保留各事件及各自核准／驗證。`freeze-readiness` 使用同一份 plan，唯讀模擬所有尚缺步驟；不要求使用者先正式寫入一半事件才能得知是否合格。

診斷保留 `runner-preflight`、`freeze-readiness`、`validate`；中斷統一使用 `resume <id>`，唯讀查詢使用 `status <id>`。日常 skill 不再要求先執行一串相同子檢查，然後再手動呼叫 writer 重做一次。依既有規則必須提前終止時，提供 `terminate --plan …` 組合 evidence-unavailable／study-terminal 的原有路徑；它不是任意失敗的自動後續動作。

第一版先完成 Development 至 freeze 的高階入口。Evaluation skill 仍需獨立角色與使用者的明確執行要求；不得由開發 skill 自動接續。既有多 trial 規則保留：每次 `development` 對應一個已登記 trial，不因簡化入口變成只能做一個 trial。

## 4. 修復 A：讓 runner 輸出一路通到正式 Trial

**問題：** preflight 接受 `{candidate, baseline}`，正式 Trial validator 接受單一 Development evidence，兩條路徑沒有共同的發布步驟。

**設計決定：** 保留 runner 的 candidate／baseline 輸出包，新增一個共用的 Development 輸出消費服務。它驗證輸出包，將 candidate 與 baseline 分別以 canonical bytes 保存，產生包含兩者 path／digest 與輸入綁定的 manifest，再把 candidate 的精確 path／digest 交給 trial-recorded。baseline 不進候選 family，但必須被正式保存與驗證，不能在拆分時丟棄。

- Schema 明確區分 runner 輸出包、單一 evidence 與發布 manifest；不得靠檔名猜格式。
- runner-preflight、正式 `development` 與恢復都使用同一消費服務，不另寫「合成資料專用拆分器」。
- preflight 先在隔離位置執行真正 runner，再用隔離的 Study fixture 通過同一 artifact／trial 驗證及發布路徑。這些 fixture Event／checkpoint 只存在於暫存測試空間，不得進入正式 repository、authority 或研究證據；報告明示為合成驗證。
- 正式 preflight 綁定測試所需的 input fixture、source、設定、工具／環境與資料指紋。建立前再次核對；另驗證正式 Development procedure 就是受測入口。
- `development` 預設先查找相同 operation 的執行紀錄；已有輸出時先驗證並完成發布，不自動重跑 runner。中斷且無完整輸出時，依 frozen-input recovery 規則判斷，不把「沒有 evidence」解讀為「沒有接觸資料」。
- 合法 gate fail／無交易是執行完成的研究結果；CLI 成功發布後不應以一般程式錯誤的 exit code 暗示 skill 可以反覆重跑。

**驗收：** 同一份實際 runner 輸出，直接走正式消費服務完成 trial-recorded、重建 validator 與 baseline 綁定；涵蓋正常、無交易、gate fail、缺 baseline、錯誤 evidence 格式、import 失敗及重複 spec。修復前的格式不相容必須成為可失敗的回歸測試。

## 5. 修復 B：從重算結果決定凍結資格

**問題：** Trial 的 `completed` 只表示執行完成；目前卻能搭配 caller 提供的合格名單，讓零交易且 fail 的候選凍結。

- 將 Development 重算結果納入可重建的 trial 判定，而不是丟棄 validator 傳回的失敗原因。
- 不以修改 Trial 執行狀態的方式掩蓋績效失敗；「完成」、「證據可驗證」、「門檻通過」與「可凍結」分開保存。
- validator 依凍結的規則重算完整候選集合的 eligibility、排序與 tie handling，核對 selection evidence；不能只確認名單中的 ID 曾經出現。
- 不支援的正式 gate、research target 計算或選擇規則，須在 prepare 就拒絕；不可等凍結才發現無法判定，也不可把未知規則當成通過。
- `candidate_available`、selection 名單及 `candidate_freeze_eligibility` 都是可被驗證的結果，不是 caller 的授權。
- baseline 不參加候選排序；證據有效性及其與預先登記 baseline 的一致性仍需驗證。

| 情況 | 證據判斷 | 凍結與後續 |
| --- | --- | --- |
| 有效且正式 gates／已登記 targets 均通過 | valid | 還須滿足完整 registry、provenance、選擇與核准等條件 |
| 有效，但正式 gates 失敗 | valid、formal fail | 不可凍結；依既有規則與 trial budget 決定後續或 terminal |
| 正式 gates 通過，但 research target 失敗 | valid、formal pass | 不可凍結；不塞入正式 failed_gates，不偽裝成 evidence failure |
| 無交易 | 可為 valid；無法估計的統計明示不可估計 | 不具候選資格，不捏造 bootstrap 或成功結果 |
| 證據缺失／損壞 | unavailable／invalid／needs-repair | 阻擋凍結；區分可恢復與不可恢復，不一律自動 terminal |

`research/tools/development_status.py` 的概念可以沿用，但 v002 需使用明確版本綁定的實作；不得直接 import 會載入 v001 validator 的共用模組。Research targets 若未登記，就明示 not_registered；缺資料與未登記不能混為一談。Blind review eligibility 仍只能依實際 outcome exposure 判斷，不由 Evaluation 是否啟動或 Study 是否 terminal 反推。

**驗收：** 無交易、任一正式 gate fail、target-only fail、無效 evidence、偽造 eligible 清單／排序均不能凍結；有效的完整候選可以凍結。低階 append candidate-frozen 與高階 freeze 要得到同樣判定。

## 6. 修復 C：重驗所有新增佐證

**問題：** prepare 與預先登記核准佐證只在寫入時檢查，檔案遺失後仍可通過 validate。

- 將 prepare-report、preregistration approval、development authorization 與必要的 plan／輸出 manifest 明確納入 schemas、證據要求及事件引用關係。
- validate 重建事件鏈時必須核對檔案存在、canonical 格式、digest、Study／Workflow／source 綁定，以及該核准究竟對應哪份規格、哪個 scope 與 actor。
- 核准依據須明確指向 Study、preregistration／source 等受核准內容，不能僅憑 `decision: approved` 和非空文字就套用到不同研究。
- 「歷史報告完整性」與「建立前報告是否仍新鮮」使用不同驗證：建立前比對目前 source／環境；重驗既有事件則比對事件綁定的歷史 bytes，不要求幾個月後的本機套件版本仍相同。
- recover 的規則同樣驗證原 prepared operation 所引用的資料；不得把完成原事件偷換成依目前檔案重新產生事件。對尚未完全發布的原 bytes，先在隔離位置驗證預計恢復的完整結果。
- 佐證損壞時不補寫成「已核准」，不根據新環境倒填舊報告；顯示具體缺失並走既有恢復／不可判定處理。

**驗收：** 分別刪除、修改或跨 Study 交換每種佐證，validate／append／freeze／recover 均拒絕不可信引用；原文件完整但目前環境改變時，歷史驗證仍成立，而新 create 必須重新 prepare。

## 7. 修復 D：真正的程序中斷與安全恢復

**問題：** 現有測試只拋出 Python 例外，仍會正常清理鎖；程序崩潰留下的鎖會讓恢復永久卡住。

- 本專案 macOS／Linux 優先採作業系統持有的檔案鎖，例如 `flock`：程序退出時釋放持鎖狀態，不能再以「鎖檔存在」代表程序存活。
- 鎖檔可保留作定位，不在解鎖時刪除或替換檔案，以免不同程序鎖到不同 inode。PID／時間僅供診斷，不據此刪除未知鎖；不支援的平台明確拒絕，不退回不安全行為。
- 高階操作與低階 writer 使用同一套 Study 鎖定協定。處理巢狀呼叫，避免 batch 已持鎖又呼叫會自行加鎖的 writer 而死鎖；內部鎖定上下文不得變成公開的「略過驗證」開關。
- 操作紀錄綁定原計畫、runner／inputs／預備 bytes 及已完成步驟。恢復只能接續同一 operation，不能重新 create、產生新事件時間、換 authority 或改 frozen inputs。
- Artifact 與事件逐步發布，各自不可覆寫；失敗訊息須列出已完成步驟、待恢復步驟及是否需要人員處理，不宣稱整批回滾。

**驗收：** 真正開子程序，在 artifact 發布、journal prepared、Event 已寫但 checkpoint 未寫、checkpoint 已寫但 projection 未更新、以及各批次步驟間，用同步屏障觸發 `os._exit`／強制終止。重啟後驗證可接續、沒有重複事件、head／checkpoint 一致；另測兩程序競爭、活鎖拒絕、不同 plan 拒絕與重複 resume。

## 8. Skill 與 CLI 的穩定交接

**建議先新增 v002 專用 skill，重用舊 skill 的研究方法，不直接把舊 skill 全面改成 v002。** 舊 skill 與 script 明確綁定 v001、`.authority/`、`studyctl all`，Evaluation skill 還硬編碼第 7／8 個事件檔名；只替換版本字串會留下錯誤流程。

建立兩個角色分離的入口：

- 開發 skill：僅 study 開發者使用；走本計畫正常 CLI 路徑，完成 candidate-frozen 或依規則處理失敗後停止，不讀取正式 Evaluation 結果。
- Evaluation skill：僅 Study 歷史評估執行者使用；必須收到明確執行要求，檢查實際事件狀態與 frozen operation，不依賴固定序號；維持一次性執行、資料隔離與結果專用 store。

新 Study 延續 repository-local `<repository-root>/.authority/` 約定；CLI 從明確的 repository context 推導並回報它，不要求 skill 每一步重新猜路徑。既有 Study 使用原綁定 root，不搬遷、不靜默切換。prepare 合併新 ID、authority、staged bundle 檢查；每次正式寫入仍在服務內驗證 checkpoint。首次建立 research 目錄用不可覆寫建立方式，避免在 prepare 前覆蓋既有 bundle。

兩個 skill 不複製 writer 邏輯；只呼叫受支持的高階命令。CLI 的機器可讀輸出需穩定提供：

- 明確 Workflow version、Study ID、operation ID、實際 authority root。
- 執行狀態、已完成步驟、目前 Event／head、需要 resume 與否。
- 正式 gates、targets、evidence validity、freeze eligibility 各自狀態及原因。
- 有穩定 code 的錯誤、相關 path、expected／actual、下一個允許的操作。
- 缺少的人員輸入／核准，以及它對應的具體內容指紋。

`status` 的下一步是建議，不是自動授權。開發者視圖不得為了顯示狀態而開啟正式結果 store；無權驗證的後續階段明示未驗證，不偽稱整條鏈已完整驗證。角色限制須落實到查詢／驗證的讀取範圍，不只隱藏畫面文字。

若未來要一個共用 skill，自動分派只能依已確認的 Workflow version 與角色；不使用 latest，也不在同一 Python process 混載兩版的 `validator`／`writer`。這是後續整合，不是本次修復的前置條件。

## 9. 實作順序與完成門檻

| 階段 | 工作與檔案範圍 | 完成門檻 |
| --- | --- | --- |
| 1. 固定契約與回歸案例 | v002 schemas／rules；將四項重現納入 tests | 修復前確實失敗；固定輸出包、發布 manifest、資格與核准綁定契約 |
| 2. 修核心不變條件 | validator/artifacts.py、validator/study.py、writer/service.py | raw 結果決定資格；所有新增引用可重驗；低階入口不能繞過 |
| 3. 修 runner 消費路徑 | operations/preflight.py、共用發布服務、正式啟動器 | 合成與正式 fixture 使用同一 runner、序列化與消費路徑，完成 trial-recorded |
| 4. 修恢復與組合操作 | writer/lock.py、journal.py、operations/service.py | 真正程序終止、併發、部分發布與相同 operation 接續測試通過 |
| 5. 整理日常 CLI | operations/cli.py、版本固定的狀態／交接資料 | 四個正常步驟可從建立走到凍結；失敗分支可診斷或安全 resume |
| 6. Skill 與文件 | 新 v002 skills、操作指南、範例與技能回歸測試 | 開發／Evaluation 角色分離；不用人工拆 evidence 或拼 writer 事件；v001 行為保留 |
| 7. 新 RC | 全部測試、Ruff、canonical／schema、Policy 一致性、manifest／report | 全部通過後交付核准者；沒有正式 release.yml 或 Active 變更 |

這是實作依賴順序，不是專案看板指派。涉及 Lifecycle、角色權限或研究結果定義的治理調整，由適當治理角色處理；本計畫不授權執行者自行放寬規則。

## 10. 發布前整體驗收

最重要的新測試是一條不中斷的隔離流程：真實 CLI prepare → 既有核准 create-authorize → 真正 fixture runner → 同一輸出消費服務 → Trial 登錄 → 完整 registry／provenance／選擇 → freeze-readiness／freeze → 重新啟動 validator 驗證。這條測試不得 monkeypatch 掉 prepare、approval、eligibility 或 artifact 檢查；同一策略引擎必須同時用於 contract 測試與 runner，不能像現有整合 fixture 一樣各測不同引擎。

另外必須涵蓋：

1. 有效成功、正式 gate fail、target-only fail、零交易、技術／證據失敗，各自走正確分支。
2. 正式 evaluator 的合成 fixture 與提前終止／terminal 接續；不使用正式資料，開發 skill 不自行執行 Evaluation。
3. 對每份新增佐證逐一做刪除、digest 漂移、錯角色／scope、錯 Study 與錯規格綁定測試。
4. 真正程序崩潰與競爭下的恢復；測試操作不碰原 repository 的 authority 或結果 store。
5. v001 suite、共用工具及舊 skills 的相容性；v002 Policy 原文保持不變。
6. Skill 的命令順序與 JSON 契約測試，以及一條以隔離 fixture 驗證的端到端示範。CLI 的安全性不依賴 skill 是否正確提示。
7. 新 RC manifest 及測試報告與當前內容一致；正規 release 驗證仍因沒有 release.yml 而拒絕啟用。

交付包含修復摘要、各反例的回歸結果、從舊操作到新 CLI 的對照、兩個角色的交接範例、限制與待核准事項。不能僅以原有測試仍通過，宣稱四個缺漏已修復。

## 11. 依據

- [Workflow Lifecycle](../workflow-lifecycle.md) 與 [RC 不自我啟用](../adr/0036-implementation-stops-at-a-release-candidate.md)。
- [v002 操作指南](../../workflows/strategy-forward-replication-research--v002/reference/operations.md)。
- [現有開發 skill](../../.agents/skills/build-strategy-study-to-freeze/SKILL.md) 與 [現有 Evaluation skill](../../.agents/skills/run-strategy-historical-evaluation/SKILL.md)：本次僅分析其規範與介面，未執行其中的 Study 操作。
- 四項 review 結果：runner 輸出無法直接登錄 Trial、fail／零交易候選仍能凍結、新佐證遺失仍通過 validate、程序退出後殘留鎖阻止恢復。
