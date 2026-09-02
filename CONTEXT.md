# 策略研究驗證

本脈絡描述一個策略研究個案如何依固定規則留下可追查的證據，並得到受限的回溯研究結論。

## Language

**Study（研究個案）**：
一次綁定特定 workflow、研究規則、資料與候選家族的完整研究生命週期。
_避免使用_：Run、單次回測

**Study Event（研究事件）**：
Study 中已經發生且不可改寫的事實，例如候選完成凍結或獨立審查完成。
_避免使用_：狀態更新、直接改狀態

**Study State（研究狀態）**：
根據 Study Events 推導出的目前階段與結果，不是可獨立修改的事實。
_避免使用_：手填狀態、權威結果欄位

**Provenance（來源可信狀態）**：
描述正式評估資料、策略與研究過程是否曾受到後段結果影響，以及是否有足夠證據判定這件事。
_避免使用_：資料品質、資料新舊

**Verified Clean（已驗證乾淨）**：
有足夠證據確認 Study 未受不當的後段結果揭露影響，可以進入正式評估。
_避免使用_：應該沒看過、研究者自稱未看過

**Known Contaminated（已知污染）**：
已有證據確認 Study 受到不當的後段結果揭露影響，其正式驗證資格失敗。
_避免使用_：仍可參考、有限通過

**Provenance Unknown（來源狀態未知）**：
證據不足，無法可信判定 Study 是否受到後段結果揭露影響，因此結果不可判定。
_避免使用_：暫時乾淨、先當作沒問題

**Workflow Floor（流程底線）**：
Workflow 對所有 Study 規定的最低合格要求，任何 Study 都不能降低。
_避免使用_：建議門檻、預設值

**Study Gate（個案門檻）**：
Study 在查看正式結果前固定的判定條件；它可以比 Workflow Floor 嚴格，但不能更寬鬆。
_避免使用_：可調門檻、事後標準

**Workflow Version（流程版本）**：
一組自包含且可由 exact digest 識別的研究規則；Study 從建立到終止都綁定同一版本。
_避免使用_：最新版、隱含版本

**Fail（失敗）**：
必要條件可以可靠判定，而且結果未達 Workflow Floor 或 Study Gate 的終止結論。
_避免使用_：無法判斷、執行錯誤

**Indeterminate（不可判定）**：
因身份、來源或證據完整性不足，無法可信判斷必要條件是否通過的終止結論。
_避免使用_：失敗、暫停

**Paused（暫停）**：
Study 因可恢復的技術問題停止推進，但尚未形成終止結論，只能用完全相同的 frozen inputs 恢復。
_避免使用_：失敗、重新開始

**Trial（策略試驗）**：
由策略、參數、資料、成本、成交與持有規則等 exact inputs 共同識別的一次結果相關試驗。
_避免使用_：程式執行次數、任意命名的版本

**Trial Retry（試驗重試）**：
使用完全相同 exact inputs 恢復或重跑同一 Trial；任何會影響結果的 input 改變都不是 retry。
_避免使用_：修改後重試、重新調參

**Candidate Family（候選家族）**：
在 preregistration 完整列出、可以依固定規則競爭成為 Selected Candidate 的 Trials 集合。
_避免使用_：所有比較策略、包含 baseline 的清單

**Selected Candidate（入選候選）**：
依預先固定的 eligibility、排序與同分規則，從完整 Candidate Family 選出的唯一 Trial。
_避免使用_：最佳回測、事後冠軍

**Baseline（比較基準）**：
預先固定、來自不同且可客觀判定為更簡單之策略 family 的比較對象，不參與 Candidate Family 排名。
_避免使用_：備用 candidate、可更換 benchmark

**Evaluation Fold（評估分段）**：
Historical Evaluation 中一個獨立年度的績效區間，不承接其他年度的交易狀態。
_避免使用_：連續回測的年度報表、可跨年持倉區間

**Fold Warmup（分段暖機）**：
Evaluation Fold 開頭只供指標累積觀察值的固定 sessions；期間不產生訊號、交易或績效。
_避免使用_：前一年度 carry、可交易暖機期

**Challenge Evidence（穩健性挑戰證據）**：
九項必要 robustness challenges 其中一項的獨立不可改寫結果，綁定同一 Selected Candidate 與正式評估 inputs。
_避免使用_：challenge 摘要、合併 passed flag

**Independent Reviewer（獨立審查者）**：
負責從 frozen inputs 與 raw evidence 重新計算最終結果的人；可以和 research owner、replay operator 或 evidence producer 是同一人。
_避免使用_：只確認既有 passed flag、不重算的審查者

**Terminal Evidence（終止證據）**：
從完整 frozen inputs 與全部必要 evidence 重算出的最終判定依據，經 Independent Reviewer 確認後才能形成 outcome。
_避免使用_：手填結果、caller-reported pass

**Evidence Manifest（證據清冊）**：
保存大型或敏感 evidence 的穩定位置、大小、SHA-256 與內容範圍，使 reviewer 能取得並驗證完全相同的 artifact。
_避免使用_：latest pointer、只有檔名的索引

**Source Bundle（程式來源包）**：
一次正式操作所使用且可能影響結果的程式、workflow、policy、設定與依賴清冊，以內容 digests 識別。
_避免使用_：最新版程式、只有 Git commit 的程式身份

**Trusted Operator（受信任操作者）**：
被信任會如實使用自己的穩定 identity，並只透過正式工具寫入 Study 的人。
_避免使用_：經密碼學驗證的身分、惡意管理者

**Qualification Metric（資格指標）**：
依固定公式、十進位精度與 rounding rule 從原始 evidence 重算，並用來判斷 Workflow Floor 或 Study Gate 的數值。
_避免使用_：顯示用百分比、呼叫者填寫的結果

**Retrospective Replay（歷史成交重播）**：
使用已結束的固定日期與 frozen inputs，依 session 順序重建 proposals、模擬 fills、positions、cash 與 ledger 的歷史研究階段。
_避免使用_：Shadow trading、forward test、實盤模擬授權

**Data Snapshot（資料快照）**：
一個資料角色在固定 sessions、欄位、調整方式與來源條件下的不可改寫市場資料集合，以 exact digest 識別。
_避免使用_：即時下載、可更新資料集

**Session Inventory（交易時段清冊）**：
Data Snapshot 預期且實際包含的完整有序交易 sessions，用來判斷缺漏、重複或額外資料。
_避免使用_：只有起訖日期、資料列數

**Market Policy（市場政策）**：
Workflow 固定的市場、資料頻率、timezone、交易日曆與價格處理規則，所有 Study 使用相同版本。
_避免使用_：Study 自選 calendar、隱含市場設定

**Policy Release（政策發布版）**：
一組自包含的 policy values、實作 bindings、conformance evidence 與 digests，供 Workflow Version 精確引用。
_避免使用_：從其他專案複製的 release 身分、implicit latest

**Workflow Package（流程套件）**：
一個 Workflow Version 自己擁有的規則、schemas、validator、writer、tests、examples 與說明文件集合。
_避免使用_：共用 state machine 的薄設定檔、依賴 implicit global rules

**Workflow Release（流程發布）**：
Workflow Package 通過必要驗證並由 trusted approver 一次性啟用的不可改寫事實。
_避免使用_：直接修改 status、資料夾存在即視為 active

**Proposal（研究建議單）**：
Historical Evaluation、challenge 或 replay 產生的不可執行交易意圖，只供模擬與研究證據使用。
_避免使用_：Broker Order、真實委託

**Proposal Order Type（建議單種類）**：
Proposal 使用的固定撮合語意；v001 只允許 `MARKET`、`LIMIT` 與 `STOP_MARKET`。
_避免使用_：Trailing Stop、Stop Limit、未登記種類
