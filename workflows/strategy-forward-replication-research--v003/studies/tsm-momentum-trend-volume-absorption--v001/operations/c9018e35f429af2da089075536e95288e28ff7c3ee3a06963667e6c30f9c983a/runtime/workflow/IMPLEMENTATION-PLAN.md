# v003 實作與驗收對照

依 `docs/plans/study-explicit-assignment-lifecycle.md`，由 workflow 執行者建立 v003 後繼版本。v002、既有 Study、已引用 Policy 與治理文件保持原樣。本次只交付 Release Candidate，不建立正式 Study、不執行正式評估、不建立 release.yml。看板沒有已指派項目，未改看板狀態。

## 契約與驗證

| 範圍 | 實作與證據 |
| --- | --- |
| 明確派工與新事件 | assignments validator、event／plan schemas、writer context；test_assignment_lifecycle 驗證新路徑與舊核准拒絕。 |
| 連續開發 | continuous 與 lifecycle 共用 prepare、writer、資格判定；完整 CLI fixture 執行固定 engine 至 freeze。 |
| 一次性評估 | 鎖內 reservation、started checkpoint、雙份 launch marker；test_crash_recovery 逐點硬中斷與並行。 |
| 保留研究資格 | candidate／baseline、registry、provenance、門檻與選擇次序仍由原 validator 判定；反例拒絕 freeze。 |
| 缺失與篡改 | 原報告、派工、登記及計畫重讀，不依賴快取 projection；authority／事件鏈與 journal 保留。 |
| 角色隔離 | 開發者 status 只重建 prefix，對假 store 的禁止讀取測試；錯誤不輸出受限內容。 |
| 發布邊界 | manifest、測試報告與 canonical／Policy／Ruff 驗證；沒有正式 release record。 |

測試 fixture 明確標示合成指令，不產生 Study approved 文件。Policy release 原樣攜入；測試中 Workflow Release fixture 只驗證發布機制，不是 Study 核准，也不寫入本 Package 的 release.yml。

全部實際命令、結果與完整性摘要見 release-test-report.yml。派工與 CLI role 不提供密碼學或作業系統身分認證。隔離 runner 沿用 v002 的 runtime 防護，正式流程仍須遵守 AGENTS.md 角色規範。
