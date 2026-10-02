# TASK-036 v006 部分 create 恢復審閱

日期：2026-10-02  
角色：專案管理者  
Study：`tsm-divergence-sma20-sma50-regime--v002`  
執行者：`/root/task_036_v006_resume`（study 開發者）

## 首次 create 的狀態

唯一失敗原因為 `copy-forward-artifact-drift`：研究目錄中的 `create-plan.yml` 與部分 Study 已寫入的恢復計畫不同。原 CLI 回報 `qualification-failed`、`operation_id=null`、`published_events=[]`、`pending_journals=[]`。Study 僅有建立 manifest、時間戳與 preregistration；沒有 `events/`、`journals/`、`operations/`，沒有 Development Trial 或 runner 證據。`.writer.lock` 不存在活躍持鎖程序。

原 create descriptor 的 operation ID 為 `426bf4bf89155a48a99a947c8dbc83fd9c691e8af92dbbcea2010f65b599165f`，仍固定原派工、計畫、報告、authority、Source Bundle、workflow 與 preregistration 指紋。未變更 descriptor 或其綁定。

## 經核准的有限修復

先前 research 計畫以原 bytes 保存至 `.study-developer/task-036-v006-resume-20261002/authority/append-only-preservation/TASK-036-v006-resume-20261002/research-tsm-v002-create-plan.pre-repair.yml`，SHA-256=`5a33c27d07a8c3aa8045dbd73af8709d31489f873f4a9c237759741254afa8af`；收據 SHA-256=`d47c15f3f0a6e13a21728d3228675e2fad42c51be9a9a8767b57ef9e5382d4de`。v002 active research 計畫現在與 Study manifest 逐 bytes 相同，SHA-256=`d1ce1899823ae7e81a0b60f4f66cb2b6352148f9daa8548cf9f4408d57720698`。派工受派者及 create／Development actor 均為 `/root/task_036_v006_resume`。candidate source diff 未變，SHA-256=`098bac59e138a7c74d69c6dbceef45d6a651ef7ef6db12bcfdd370a58a3a410d`。

此修復只校正目前 v002 的 create-plan copy-forward；未改 candidate、Development 計畫、preregistration、Source Bundle、資料、Study manifest、既有報告或 Workflow／Policy。舊 v001／v005 紀錄與 v009 原始程式維持保留。

## 完整 prepare 的 PM 核對

修復後完整 prepare 再次通過，`prepare_checks=passed`；native precreate 的 contract 與 synthetic 子檢查均 passed、0 errors／warnings，`native_synthetic` passed。新報告位於 `.study-developer/task-036-v006-resume-20261002/prepare-report-copy-forward-repair-20261002.yml`，SHA-256=`d12e8ee571dab1691f2d970d462bdf303d65c70fca8ba7a77174340cbd03ca5f`。新舊報告的 binding、runner cases 與 `native_synthetic` 完全相同；完整 YAML 唯一差異是 23 個參數對照的 `expected_path` 從 research preregistration 改為已發布、同內容的 Study preregistration manifest，對照值未變。

Study 的原 prepare report 仍是 operation 所綁定的報告，SHA-256=`256c07fa8dae958825fe8f7b064622337bfbf362db9857bada71572bbbb842d1`；`create-operation.yml.report_digest` 也維持此值。新報告沒有取代或改寫原報告。PM 檢查 v006 `verify_report()`：恢復時會驗證 report Schema、passed 狀態、prepare 狀態、目前 binding、runner cases，並重新產生 native precreate 結果，要求它與原報告的 `native_synthetic` 完全相同。上述條件現均成立，故同一原報告仍可合法恢復原 operation。

本次有效 v006 Release／manifest／test report、Workflow／Policy／reference digests、固定資料 digest 與 Source Bundle 綁定均與 TASK-041 驗收及 Stage A PM 審閱相符；Source Bundle 11/11 檔案指紋及 candidate 與 v009 的唯一策略差異已審閱。Control 仍由正式 runner 直接使用未修改的 v009 `DEFAULT_SPEC`。

## PM 決定

審閱通過。授權 worker 使用原 repo、原 authority、原 assignment，透過 v006 的正式 `resume` 恢復 operation `426bf4bf89155a48a99a947c8dbc83fd9c691e8af92dbbcea2010f65b599165f`；不得直接再呼叫 `create`。resume 成功且三個預期 create Events 完整後，可依原 Development plan 執行唯一 Trial 一次。若 resume 回報資格／綁定／恢復錯誤，或發現 Trial／runner 已存在，須停止且不得再寫 Study。Development 完成後仍維持 Doing，交 PM 驗收；不得 freeze、Historical Evaluation、Terminal、challenge 或 replay。
