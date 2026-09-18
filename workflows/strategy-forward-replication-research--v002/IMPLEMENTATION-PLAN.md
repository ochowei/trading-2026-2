# v002 實作與驗收紀錄

## 交付界線

目標為可供核准者審查的 Release Candidate；以 `release-manifest.yml` 與 `release-test-report.yml` 是否存在且驗證一致判定。沒有正式 `release.yml`，不代表 Active，不取代 v001，也不建立任何正式 Study。

本工作以 workflow 執行者身分執行既定 Lifecycle。沒有修改外部治理文件、已引用 Policy、v001、既有 Study、authority 或 evidence。共享看板目前沒有被指派任務，因此未新增、搬動或驗收看板項目。

## 實作內容

- 本版自包含保存 rules、schemas、Policies 的相同 bytes、validator、guarded writer、tests 與操作文件。未複製既有 Studies、結果或 Workflow release 記錄。
- 本版的 `operations/legacy_checks.py` 固定保存原有 precreate、策略 contract 與合成邊界檢查；不修改共用 v001 工具，避免載入不同版本的 validator。
- `prepare` 加入完整 runner 合成執行、原始證據重算及報告綁定。Development 與 Historical 走相同的正式啟動介面，至少涵蓋有交易與無交易。
- writer 在第一個事件前核對 prepare 報告；低階 create 不可略過。核准事件要求實際提供 actor、scope、decision、role、時間與依據，批次入口不自行核准。
- `create-authorize` 保存不可改寫計畫，逐事件發布並沿既有 journal 恢復。事件種類與狀態模型不變，不宣稱跨事件原子性。
- `freeze-readiness` 使用完整鏈、checkpoint 及真正的 candidate-frozen transition 驗證，不只確認既有鏈沒有錯誤。
- 空交易 Development evidence 明示統計不可估計與資格 fail；其他 source、inputs、trial、provenance、選擇、raw evidence 重算與提前終止規則維持。

## 驗收對照

| 需求 | 證據 |
| --- | --- |
| import／spec 重複／錯誤 evidence 在第一事件前攔截 | `test_runner_fault_precedes_first_event` |
| 合法無交易與績效 gate fail | `test_real_cli_runs_both_stages_and_accepts_gate_fail_and_no_trades` |
| source／設定變更後拒絕 create | `test_create_rejects_stale_report_before_any_event` |
| prepare 失敗無事件、checkpoint、成功報告 | `test_prepare_failure_does_not_publish` |
| 完整 prepare 串接三事件 | `test_complete_prepare_then_create_without_skipping_contract` |
| 三個批次步驟中斷後接續、不重複事件 | `test_batch_recovers_exact_events_without_duplicates` |
| 無核准不建立第一個事件 | `test_batch_rejects_missing_approval_without_first_event` |
| 低階 writer 不可跳過 prepare | `test_writer_cannot_bypass_prepare` |
| freeze-readiness 真正判定凍結資格且不寫入 | `test_freeze_readiness_uses_actual_transition_without_writing` |
| 正常、提前終止、checkpoint、不可覆寫與 recovery | 本版保留的 `test_study_end_to_end.py`、`test_integrity_and_recovery.py` |
| Policy 一致性與自包含 | `test_policy_conformance.py`、`test_release_candidate.py` |
| v001 相容性 | 另以獨立 Python process 執行 v001 suite 與既有 studyctl／termination_preflight／package tests |

最終命令、結果與時間記錄於 `release-test-report.yml`。既有 transition 單元測試使用暫存服務與 fixture 核准；為聚焦既有事件語意，其 fixture 關閉新入口前置檢查。新增 `test_operations.py` 的 runner／writer 整合案例不套用該共用 fixture；完整 prepare 案例實際執行 contract、策略合成檢查、runner subprocess、canonical YAML 及 validator。

測試使用最小 fixture runner 與獨立的策略 contract fixture，驗證的是操作工具的整合，不是任何既有 TSM Study 的績效或 runner 已獲認證。每一個未來 Study 都必須以自己的 frozen runner 和合成案例通過 prepare。

## 限制與待核准事項

1. 新 v002 runner 需要接受 request/output 固定介面；不自動改寫既有 v001 runner，也不把它們視為已通過完整 preflight。
2. Python audit hook 是可信 runner 的誤用防護，不抵抗惡意原生程式。正式環境仍需離線且沒有券商權限，並只提供當階段的資料。
3. 合成案例的價格與日期必須由開發者事前設計，涵蓋策略的重要分支；工具不會替任意策略保證分支完整。無交易與有交易至少都要實際觸發。
4. 既有 bootstrap 測試使用無虧損樣本時，NumPy 的無窮大分位數會發出 RuntimeWarning。既有規則與重算結果保持一致；不將警告隱藏或宣稱已修復數值模型。
5. 批次中斷後，原 source、工具環境、設定、plan 與核准依據都需保留。不可恢復的變動走既定 evidence-unavailable／terminal；不得以重建掩蓋已接觸的資料。
6. 核准者需審查新 runner 介面、無交易表示、核准文件與報告綁定規則，再決定是否建立 release。舊版是否 Superseded 由治理角色另行處理。

未發現需要改變研究目的、階段、事件種類或結果權限的必要性，因此維持同一 Workflow 的 v002。將三個事件合併或引入跨事件交易屬於未來治理提案；本版不執行。

## 本次實際驗證結果

v002：57 passed（9 個既有 NumPy 警告）；v001 與共用工具：58 passed（8 個既有警告）；Ruff 通過。Workflow schema、canonical YAML、Policy digest 與 Policy 原文一致性均已驗證。測試使用已存在的 Python 3.11 環境，未下載依賴或使用正式行情。
