# v002 修復實作與驗收紀錄

本次依 `docs/plans/v002-workflow-repair-plan.md` 修復提交 `4372f6b` 的四個缺漏，交付重新驗證的 Release Candidate。原 RC 報告不再代表新內容；正式啟用仍須核准者建立 release.yml。本次沒有建立正式 Study、執行真實 Historical Evaluation、變更 Lifecycle、v001 或已引用 Policy。共享看板無被指派任務，未移動任務。

## 四項修復

| 原問題與影響 | 實作 | 回歸證據 |
| --- | --- | --- |
| runner 的 candidate／baseline 輸出包不能直接登錄 Trial | 共用 consumer 保存兩份 canonical evidence、inputs、publication manifest；preflight 亦實際發布隔離 Trial 並驗證 | 完整 CLI fixture、baseline 遺失、錯格式／import／重複 spec 反例 |
| completed 的零交易／fail Trial 可冒充合格候選 | raw evidence 重算 formal gates、targets、完整 eligible 集合、排序／同分規則；registry 與低階 freeze 皆核對 | no-trades、gate-fail、target-only、偽造 selection、多 Trial 同分 |
| prepare／approval 遺失仍 validate 成功 | schemas 與事件重建重新核對原文件及 Study／source／preregistration 綁定；新 create 才要求環境新鮮 | 四種佐證各刪除／改寫、跨研究核准、歷史環境改變仍可驗證 |
| 硬中斷留下鎖而永久卡住 | 固定 inode 的 OS flock，同執行緒巢狀共用；recover 先在隔離副本驗證原 journals 的完整結果 | 子程序 os._exit 在 artifact／prepared／event／checkpoint／事件間中斷、SIGKILL 活鎖競爭、freeze 批次恢復 |

## 操作整合

日常流程改成 prepare → create-authorize → development（每個 frozen Trial）→ freeze。freeze 內含唯讀 readiness，使用者不必先寫入 registry／provenance 再查凍結資格；仍保留全部底層事件與獨立驗證，不宣稱跨事件原子性。

新增 status／validate／resume／terminate；相同 operation 已有輸出時只完成發布，不重跑 runner；started 但缺輸出時要求人工判定，不推定無 exposure。候選不合格可依完整 registry 終止為 fail；不可恢復缺 evidence 沿原事件路徑終止為 indeterminate。

新增兩個 v002 skills，package 內版本受 manifest 綁定，repository `.agents/skills` 保留同樣內容供探索。開發 skill 到 candidate-frozen 停止；Evaluation skill 僅在既定角色及使用者明確要求後呼叫獨立 Historical Evaluation 命令。Evaluation 結果及 runtime 存專用 store，依真實事件狀態接續，不硬編碼事件序號。角色參數是 CLI 範圍控制，不是身分認證。

## 測試設計

最重要的 `test_cli_prepare_to_freeze_same_engine_without_guard_bypass` 從真實 CLI prepare，走過核准、真正 runner、consumer、Trial、registry、provenance、freeze，最後重新啟動 validator。策略合約與 runner 使用同一個 frozen engine；沒有 monkeypatch prepare／approval／eligibility。固定 fixture 的研究門檻只用於測試工具，不代表正式策略績效。

`test_repairs.py` 另含完整 family、多 Trial、合法失敗、跨 Study 核准、缺失佐證、硬中斷、早期終止、合成 Evaluation 與開發者讀取邊界。原 transition 單元案例保留明示的合成 prepare 報告與核准，僅隔離昂貴 runner freshness；歷史佐證、approval、raw evidence、qualification 與 publication 驗證仍執行。新整合案例不使用該 fixture。

v001、共用 studyctl／termination_preflight、舊 skills 與 development_status 另在獨立 Python process 測試，避免兩版同名 validator 混載。實際命令、數量與結果以新 `release-test-report.yml` 為準。

## 限制與待核准

- 全部驗收僅用隔離合成資料。任何未來 Study 都必須用自己的 frozen runner 與事前設計的分支案例通過 prepare；不能以這份 RC 當作任意策略認證。
- 無完整 runner 輸出的中斷不會自動重跑；這是保留資料接觸事實的一次性執行界線，需依原 operation 判定可恢復性或走缺證據終止。
- 核准文件保存可追查的角色／scope／指紋陳述，未新增密碼學簽章或 OS 使用者認證。原有研究治理責任仍適用。
- Python audit hook 防止可信 runner 誤用；正式執行仍需要離線、沒有券商權限的環境，不聲稱可隔離惡意原生擴充。
- 既有無虧損樣本的 NumPy bootstrap 無窮大分位數警告保留，沒有修改統計模型或隱藏警告。
- 核准者需審查新 manifest、測試報告、操作／恢復與 skills 的角色界線，決定是否正式啟用；v001 是否 Superseded 由治理角色另行處理。

研究目的、資料切割、底層事件及結果定義不變，維持 v002。未發現必須改變狀態模型才能修復的治理衝突。
