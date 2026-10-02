# v006 新版 Workflow 計劃：補足長期趨勢條件的合成驗證

- 建立日期：2026-09-30
- 規劃角色：專案管理者
- 計劃狀態：2026-10-02 v006 Active、v005 Superseded，TASK-037 至041已驗收Done。依使用者最新要求暫停；TASK-036 停在create前，準備保留、Pending，等待明確恢復。
- Workflow ID：`strategy-forward-replication-research`
- 預定新版本：`v006`
- 目標 Package：`workflows/strategy-forward-replication-research--v006/`
- 觸發任務：TASK-036「測試 SMA(20) 高於 SMA(50) 的均值回歸 regime 濾網」。

## 實際問題與目前證據

TASK-036 要在原本的反轉策略上增加一個市場狀態條件：訊號日的 20 日簡單移動平均價必須高於 50 日簡單移動平均價。這裡的 regime 指策略允許進場的市場狀態。這個條件需要足夠的過去資料，也需要合成價格資料能同時形成長期上升趨勢、短期回檔與反轉訊號。

目前建 Study 前的檢查（`precreate`）在訊號與持有／冷卻兩個情境回報 `synthetic-fixture-invalid`，意思是人造測試資料未能形成符合策略契約的案例。共享看板另記錄：專案管理者已獨立重跑同一檢查；其他契約、身份、參數及 11 個來源檔案的數位指紋檢查通過，隔離執行器（runner）檢查及候選專用合成檢查也通過。正式 Study 尚未建立。

v005 公開程式的通用資料產生器主要使用平坦價格搭配單日急跌／反彈；持有與冷卻案例沿用這種形狀，而且第一個訊號的搜尋從固定第 40 個位置開始。這些設計可能不足以涵蓋 50 日均線所需的資料與趨勢條件。目前把「通用合成案例覆蓋不足」列為待證實的根因；TASK-037 必須先核對執行路徑、引擎規格與實際指標，再以最小合成案例證實。

規劃依據只有共享看板、公開 Workflow 程式與治理文件。worker 的完整派工內容保存於共享看板，不以這份專案管理者專屬計劃作為必讀文件。workflow 維護者與執行者的重現材料限公開程式與合成案例，不讀取 `.study-developer/`；study 開發者依自身角色處理該資料夾。

## TASK-037 已確認結果與目前進度

2026-10-02 使用者最新要求「在完成 Task-041 之後先暫停」。TASK-041 已Done；PM 立即中斷TASK-036執行者，尚未授權create，沒有正式Study或Development Trial。worker已交的建立前checkpoint與新research準備保留，檢查點另保存PM專屬目錄以便恢復，尚未完成PM驗收。本次只記錄暫停與保存既有成果，不執行其他工作；TASK-036已由Doing移回Pending，等待使用者明確恢復。

2026-10-02 TASK-041 驗收 Done：新歷史評估 skill 格式、契約與獨立三情境審閱通過，145項保護指紋不變。依使用者順序重新派工 TASK-036，以新v006研究ID `tsm-divergence-sma20-sma50-regime--v002` 保留v005/v001準備歷史，明確允許49-session暖機及來源綁定一致性修補，固定原v009 Control和唯一SMA20>SMA50差異。先完整建立前檢查與PM checkpoint，再唯一Development及盲檢討／成果卡；不freeze或評估。

2026-10-02 使用者要求先做 TASK-041，再做 TASK-036。PM 已派固定 workflow 維護者 `/root/task_041_v006_evaluation_skill` 建立 v006 歷史評估技能；沿用 skill-creator 與公開發布契約，僅制定操作指引。TASK-041 驗收 Done 後再重新派工 TASK-036；目前不啟動 Study 或正式評估。

2026-10-02 TASK-040 驗收通過：三份 v006 skills 及 UI metadata 已安裝，格式3/3通過；PM 契約與139項保護指紋核對通過，獨立 study 開發者三個假設情境審閱未發現阻塞問題。任務移至 Done。TASK-036 的正式 Release 與技能前置條件齊備，待明確重新派工；TASK-041 仍 TODO。本次未執行真實 Study。完整結果見 [TASK-040 驗收](../reviews/task-040-v006-skills-acceptance.md)。

2026-10-02 使用者要求「進行下一步」，PM 已派 `/root/task_040_v006_skills_developer` 處理 TASK-040。依 skill-creator 與 Active v006 公開命令、Schema 及 reference 建立開發、盲檢討、成果卡三份專用 skills，保留 v004／v005 指引；不執行真實 Study，完成後由 PM 驗收。TASK-041 尚未分派，TASK-036 維持 Pending。

2026-10-02 正式啟用與交接驗收完成：本次核准者 `ochowei@gmail.com`、核准 UTC `2026-10-02T03:25:11Z`，實際啟用 UTC `2026-10-02T03:30:52Z`。新增正式 Release 指紋 `61d6eeebe58fdd40d6805ca461ccc9a327b9aa153eedd6414a612ddc5ad3594f`，原三個核准指紋與全部保護基準不變；兩份治理文件精確符合已審閱提案，v006 Active、v005 Superseded。正式九項命令及 PM 獨立驗收均通過，TASK-039 移至 Done。完整結果見 [TASK-039 正式啟用驗收](../reviews/task-039-v006-activation-acceptance.md)。TASK-040／041 仍 TODO，TASK-036 仍 Pending；本次沒有建立真實 Study、重跑完整 pytest 或 commit。

2026-10-02 使用者要求「開始進行下一步」，PM 已指派原 workflow 執行者接續 TASK-039。先完成 RC 與保護基準重驗、Release Record 草案及具體啟用／文件變更準備，再向核准者提供最終三個指紋及可審閱內容。一般開始指令不代替 Lifecycle 規定的本次獨立核准；核准者身份及時間等待真實新核准，不沿用 v005。核准前 v006 維持 RC、v005 仍 Active，不建立根層 release.yml 或真實 Study。

2026-10-02 啟用前具體草案已收齊：待核准的 Release Record 模板、兩份治理文件差異與完整預覽、核准後 Active 驗證方式及七項隔離示範。PM 獨立重驗 RC／保護基準、模板欄位與治理提案均通過；現在只等待本次新的獨立核准，再指派正式落檔。完整指紋、影響與可審閱材料見 [TASK-039 啟用前審閱](../reviews/task-039-v006-preactivation-review.md)。

2026-10-02 使用者透過本次核准詢問明確回覆「核准 v006: ochowei@gmail.com」，對應詢問中列出的三個完整指紋及 v006 Active／v005 Superseded 交接。PM 收到回覆後即刻記錄 UTC `2026-10-02T03:25:11Z`，保存原始回覆與範圍，重新驗證所有指紋及保護基準仍相符，再授權原 workflow 執行者正式新增 release.yml。前段「等待核准」是本次回覆前的紀錄；執行者交付後再做獨立 PM 驗收。

2026-10-01 最終 RC 驗收完成：第三輪完整 Draft 為 207 passed／212 warnings（629.83 秒），執行者完整 RC 為 207 passed／212 warnings（822.51 秒），PM 獨立完整 RC 為 207 passed／212 warnings（801.75 秒）；三套均零失敗／錯誤／略過，逐案確認為相同 13 個檔案、207 個唯一案例。兩套 RC 使用同一份固定初版檔案，結果收齊後才定稿報告；完整歷史與最終三個指紋見 [TASK-038 驗收紀錄](../reviews/task-038-v006-release-candidate-acceptance.md)。PM 完成定稿 Schema／manifest／候選 checker／Ruff／既有 v005 與 Policy 基準核對後，將 TASK-037 修正與 TASK-038 移至 Done。v006 為 RC，v005 仍 Active；新核准、正式啟用與版本專屬 skills 依後續任務另行分派。

2026-10-01 第三輪完整 Draft 通過時，唯一第二輪失敗是新觀察測試把完整原生檢查次數寫少，已精確修正為每 consumer 四次、外層建立三次；最新凍結指紋為 `e527578ca62d907d5b1e16f57d5a4c52f0b7cabb9d616970eb2eb2e383f8e7a9`。當時才形成 RC 初版，後續完整 RC 與 PM 獨立驗收結果以上段為準。

2026-10-01 原維護者已完成整合修正：共用測試來源改走真正的 prepare、資格與來源指紋一起重綁、macOS 根路徑別名一致解析並保留根外拒絕、README 按發布條件檢查，另補 SMA 完整管線與 16 資產成功案例定義。三個限定開發測試為 75 passed／0 failed／0 warnings，Ruff、122 檔定義 checker 與 63 份 AST 通過。PM 獨立重算凍結指紋為 `bcbc215e2ccf0c50317212d3d6c7d792442d826e39770787e3a4668082ea76a9`。完整整合仍由同一 TASK-038 執行者驗證，限定開發通過不能取代整套發布證據。

2026-10-01 TASK-038 第一輪全套為 83 failed／108 passed／15 warnings，完整失敗日誌已保留。這是發布整合測試失敗數，不能和原 SMA 案例搜尋混為一談。主要為舊 dummy 契約／成功旗標不符新增原生 guard，另有事前登記指紋、README 斷言及 macOS 暫存根別名未一致解析的 CLI 問題；新 regime 完整管線也需補證據。TASK-037 重新開啟，由原維護者修正未發布的 Draft，TASK-038 隨後對新定義重跑。原 66 項開發驗收如實保留，v006 仍未形成 RC。

2026-10-01 使用者要求繼續 TASK-038，專案管理者已指派 `/root/task_038_v006_executor` 以 workflow 執行者角色進行完整發布候選版驗證。派工前 v006 仍為原 119 個定義的 Draft，沒有發布檔案或真實 Study；定義指紋與 TASK-037 驗收時相同。完整檢查通過後才形成 RC，交由 PM 獨立驗收；若需要修改定義，交回 workflow 維護者並重新完整驗證。

2026-09-30 已獨立重現舊原生搜尋的 8 個訊號案例與 160 個持有／冷卻案例：平坦價格加回檔使 SMA20=99.25、SMA50=99.70，候選沒有原始／接受訊號，同資料 Control 有訊號。根因確認為人造價格不足以形成長期上升環境，並有暖機推導未納入 SMA50 的缺口；單純重新執行同樣輸入不能解決。上述最初段落保留規劃當時的證據與待確認假設，結論以本節和驗收紀錄為準。

v006 Draft 已補上完整 regime 契約、最長就緒與實際均線／訊號／交易檢查、來源及原生報告綁定、CLI、範例與治理規格。PM 重跑 66 項開發測試全部通過，無 warnings；Ruff、119 檔定義 checker、60 份 Python 語法解析通過。v005 的 102 份受保護定義、三份發布檔案與八份 Policy／Release 未變，v005 仍 Active。完整驗收見 [TASK-037 驗收紀錄](../reviews/task-037-v006-draft-acceptance.md)。

SMA50 含當日收盤，需有 50 列資料、最早 index=49 就緒。原公開候選的 25 日暖機在 v006 仍被拒絕，恢復 TASK-036 時需在正式建立 Study 前，由 study 開發者依新派工重新準備一致的暖機與候選契約；這不授權更改研究假說、交易門檻或已存在的正式研究。完整 prepare／consumer／create 整合與 RC 後重跑已由 TASK-038 通過；測試管線的 baseline 是候選自身 BASELINE_SPEC，同資料公開 v009 Control 是直接引擎比較，原 TASK-036 的正式 baseline 管線仍待重新派工。正式啟用待 TASK-039；四個版本專屬 skills 仍由 TASK-040、TASK-041 建立。

## 版本基準與改動範圍

Draft 指正在開發的版本；Release Candidate（RC）指完整驗證後等待獨立核准的候選版；Active 指有有效發布核准、可供新 Study 使用的版本。目前 Active 為 v005，其 Release Record 綁定以下數位指紋：

| 內容 | SHA-256 數位指紋 |
| --- | --- |
| Workflow | `2441c16d2c477afef9d4d9ca159e3a8bff150080b8552991d5da5fbcc9daf2c2` |
| Release manifest | `6cf440bf81e2c081ff6e77025c5779cf5f2e4849015278419b836c0777db6405` |
| Test report | `3120c4edf745f3b2ae8701a7d37ac54737180a15b204bfcea46bb6619b3872dc` |

研究目的、資料角色、研究階段與結果定義相同，因此建立同一 Workflow ID 的下一個版本。v006 的能力範圍限定為合成驗證的資料構造、暖機與案例選擇、失敗診斷，以及必要的契約、範例與文件。

v006 必須是自包含 Package：包含自己的規則、Schema（資料格式與必填內容的定義）、驗證工具（validator）、受保護寫入工具（writer）、操作程式、測試、範例與參考文件。從 v005 取用定義時，以發布清單列出的內容為基準；新的 Package 不帶入舊 Study、真實結果、操作日誌、本機權威檢查紀錄（authority）或舊版本的發布證據。Policy 已被引用的內容與其固定版本、數位指紋完整保留。

候選資格、開發階段正式門檻（Development gates）、正式評估限制、資料區間、成本、風控與 1–16 個資產的資料能力沿用 v005。TASK-036 仍只有 SMA(20)>SMA(50) 這個既定差異；其比較基準（Control）、持有、停損／停利與其他策略參數依原派工固定。

## v006 必須提供的驗證能力

1. **先證實阻塞來源。** 在隔離暫存環境，以共享看板的策略條件與公開程式建立最小案例。記錄 v005 使用的引擎、引擎規格（spec）、契約、暖機要求、合成資料與實際訊號。若發現是準備或呼叫方式錯誤，將證據回報專案管理者調整計劃，不能把未確認的根因直接寫成已證實的 Workflow 缺陷。
2. **構造符合契約的價格資料。** 優先擴充 Package 內建、可重現的資料產生器，讓長期上升趨勢能與短期回檔、反轉並存。至少涵蓋 SMA(20)>SMA(50)。資料生成與案例選擇依明確契約運作，不依 TASK／Study ID 特判。
3. **由真實指標決定訊號。** 每個預期訊號都要由策略引擎的指標函式實際計算，再由回測函式決定是否接受。保留合成資料、均線值、原始／接受／拒絕訊號及理由，供他人重算。
4. **依最長暖機要求安排案例。** 第一個測試訊號須在所有必要指標都可計算後才出現。持有與冷卻測試的時間位置由契約與引擎規格推導，避免固定位置早於 50 日均線可用時間。
5. **同時驗證符合與不符合條件。** 合成案例要證明：符合長期趨勢條件時能接受合法反轉；均線關係不成立或相等時，候選會正確拒絕。以相同資料檢查較簡單的 Control，確認拒絕原因確實來自新增條件。
6. **保持失敗診斷與阻擋。** 資料未滿足契約、策略指標／接受規則錯誤、工具不支援某種契約，必須能區分。無法形成有效案例仍阻擋建 Study；候選自行提供的成功報告不能取代原生檢查。新增來源或契約欄位須經 Schema、固定程式來源及指紋的清單（Source Bundle）與數位指紋綁定。

## 最低驗收案例

| 情境 | 必須確認的實際行為 |
| --- | --- |
| 原有反轉策略，未啟用長期趨勢濾網 | 既有合成驗證與原有測試仍可通過。 |
| 長期上升趨勢＋短期超跌反轉 | 指標已就緒、SMA(20)>SMA(50)，引擎產生原始訊號並按契約接受。 |
| 相同反轉形狀，但 SMA(20)<SMA(50) | Control 可產生訊號，候選因新增條件拒絕。 |
| SMA(20)=SMA(50) | 驗證嚴格大於的邊界，候選拒絕。 |
| 50 日指標尚未就緒，及剛達可用時間 | 資料不足時無訊號；到達契約要求後使用正確的資料計算，沒有未來資料混入。 |
| 持有時間與冷卻期間 | 形成兩筆合法交易；第一筆按持有規則退出，冷卻未滿的訊號被拒絕，冷卻完成後下一筆按下一交易日開盤進場。 |
| 合成案例無法滿足契約 | 清楚回報案例無效並阻擋 prepare／create，正式 Study 沒有新事件。 |
| 指標已產生原始訊號，但接受規則被刻意破壞 | 清楚回報策略實作問題，不能歸為單純案例無效。 |
| 契約、來源、release 或資料指紋被替換 | 既有綁定檢查拒絕，不能以更換資料或成功報告繞過。 |
| 單資產與 1–16 個資產的原有路徑 | 既有相容性、隔離、日期對齊與超額拒絕測試完整保留。 |

上述案例是工具驗收，不代表策略已通過 Development gates 或具備凍結資格。

## 任務、角色與依賴

| 任務 | 負責角色 | 交付與接續條件 |
| --- | --- | --- |
| TASK-037：確認根因並建立 v006 Draft | workflow 維護者 | 交付可重現的根因證據、完整 Draft Package、上述案例與發布操作規格。制定規格及執行開發層級測試；交由執行者處理 Lifecycle。 |
| TASK-038：形成並驗收 v006 Release Candidate | workflow 執行者 | 依 TASK-037 定義的規格完整驗證，產生 manifest／test report，交付最終三個數位指紋。 |
| TASK-039：依獨立核准啟用 v006 | workflow 執行者 | Trusted Approver 檢視 TASK-038 最終內容並明確核准後，建立及驗證 Release Record，再更新治理狀態。 |
| TASK-040：建立 v006 Development、盲檢討、成果卡指引 | study 開發者 | 依 v006 實際 CLI 與契約建立三個版本限定的 skills，並對 Active Release 完成最終核對。 |
| TASK-041：建立 v006 Historical Evaluation 指引 | workflow 維護者 | 依公開規格建立評估角色使用的 skill，保留唯一評估操作、恢復方式及結果儲存界線。 |
| TASK-036：恢復原定 SMA regime Study | study 開發者 | TASK-039、TASK-040 驗收 Done 後，由專案管理者重新分派；先在 v006 通過完整建 Study 前檢查。 |

TASK-037 經專案管理者驗收後才進 TASK-038。TASK-040／041 可在 TASK-037 的介面穩定後準備文件；以 TASK-039 的有效 Release 為最終核對基準。TASK-041 是正式評估操作準備，不是 TASK-036 僅做 Development 的前置條件。

2026-09-30 使用者要求只派遣 TODO 第一項 TASK-037，已由唯一 workflow 維護者 subagent `/root/task_037_v006_maintainer` 完成 Draft；專案管理者當日獨立驗收通過並移至 Done，當時 TASK-038 至 TASK-041 尚未指派。2026-10-01 使用者要求繼續 TASK-038，由唯一 workflow 執行者 `/root/task_038_v006_executor` 接手；整合失敗交回原維護者重開 TASK-037 修正，最終兩項均通過 PM 驗收。TASK-039 至 TASK-041 尚未分派。後續每次派工仍須核對版本、有效 Release 與任務範圍，明確指定一個角色；worker 完成後維持 Doing，由專案管理者驗收。

## Release Candidate 與啟用程序

TASK-038 的 workflow 執行者先在 Draft 狀態核對自包含內容、canonical YAML（有固定格式的 YAML）、Schema、Policy、事件與綁定檢查。執行完整必要測試、Ruff 程式檢查，以及 definitions checker。端到端 create／Development／Evaluation／Terminal 測試只使用隔離副本與人造資料。

預定檢查命令如下，執行前由 worker 對照 v006 實際介面：

```sh
.venv/bin/python -m pytest workflows/strategy-forward-replication-research--v006/tests -q
.venv/bin/ruff check workflows/strategy-forward-replication-research--v006
.venv/bin/python workflows/strategy-forward-replication-research--v006/operations/release_candidate.py
```

Draft 檢查通過後，才產生新的 `release-manifest.yml` 與 `release-test-report.yml`。這兩份檔案存在時再跑完整測試、Ruff 與 `release_candidate.py --candidate`，記錄命令、退出碼、通過數、warnings、日誌指紋與真實結果。測試報告定稿後重新驗證報告 Schema、manifest 與 checker；若受保護內容再改動，重新產生證據並驗證最後內容。

TASK-039 的獨立 Trusted Approver 必須檢視最終規則與測試報告，對當下 Workflow、manifest、test report 三個數位指紋給出新的明確核准。v005 的核准不適用於 v006；核准者身份與時間依實際核准記錄。取得核准後由 workflow 執行者按既定流程落檔，使用 `validate_release_record` 驗證；已有 `release.yml` 的階段使用 Active 驗證路徑，因現有 RC checker 會拒絕正式 Release Record。

v006 驗證為 Active 後，執行者依維護者制定的 Lifecycle 更新 `docs/workflow-lifecycle.md` 與 `workflows/README.md`，記錄 v005 停止接受新 Study 的時間及 v006 取代原因。v005 原 Package、Release Record 與既有 Study 原地保留，既有 Study 繼續綁定 v005。

## TASK-036 恢復條件

1. TASK-039、TASK-040 已由專案管理者驗收 Done；v006 的有效 Release 可獨立驗證。
2. 確認 `tsm-divergence-sma20-sma50-regime--v001` 仍未正式建立；若已存在正式事件，先回報專案管理者，依原 Workflow 綁定處理。
3. 專案管理者明確重新分派 v006；study 開發者在自己的合法範圍保存新版本派工與準備文件。舊 v005 準備紀錄保留，新版重新計算 Workflow／release／source／data 綁定。
4. 固定原有研究假說與交易參數；先依最長指標需求，由 study 開發者在新的明確派工下重新準備暖機及一致的候選／事前登記／來源契約，再執行 v006 `precreate`、runner preflight、`prepare`。不可直接沿用公開候選的 25 日暖機或借用測試規格宣稱通過。完整成功後才建立唯一 Study、執行唯一 Development trial、驗證 evidence、完成盲檢討與 append-only（只追加）的成果卡。
5. 依正式 gates、研究目標、證據有效性與來源暴露情形如實判斷凍結資格；工具檢查成功不會消除原有來源不明或資格限制。結果仍由專案管理者驗收。

## 專案管理者驗收重點

- 根因有可重現證據；完整檢查仍會拒絕錯誤策略、無效案例與綁定漂移。
- v006 定義、版本引用、發布清單與最終測試報告一致，v005 受保護內容與固定 Policy 指紋完整保留。
- Draft、RC、Active 三個階段各有對應實際證據，沒有提前建立正式 Study。
- worker 交接只引用允許範圍；不讀取 `.super-admin/`、`historical-evaluation-artifacts/` 或其他角色的專屬資料夾。
- TASK-036 在新版 Active 與操作指引就緒後，依原定假說接受重新派工。

## 依據

- `AGENTS.md`：角色、看板及專屬資料夾的限制。
- `.project-manager/PROJECT_KANBAN.md`：TASK-036 阻塞紀錄與 TASK-037 至 TASK-041 共享派工規格。
- `docs/workflow-lifecycle.md`：版本不可變、Draft／RC／Active、獨立核准與既有 Study 綁定規則。
- `workflows/strategy-forward-replication-research--v005/release.yml`：基準版本與數位指紋。
- `workflows/strategy-forward-replication-research--v005/operations/legacy_checks.py`：通用合成資料、訊號與持有／冷卻檢查及錯誤分類。
- `workflows/strategy-forward-replication-research--v005/operations/release_candidate.py`、`IMPLEMENTATION-PLAN.md`：Draft、RC checker 與發布前檢查要求。
