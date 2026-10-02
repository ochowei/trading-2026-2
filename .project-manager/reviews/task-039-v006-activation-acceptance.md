# TASK-039：v006 正式啟用專案管理者驗收

- 日期：2026-10-02（Asia/Taipei）
- 驗收角色：專案管理者
- 執行者：`/root/task_038_v006_executor`，沿用 workflow 執行者角色接續 TASK-039。
- 狀態：完整交付通過 PM 獨立驗收；TASK-039 移至 Done。v006 Active、v005 Superseded。

## 實際結果與影響

v006 已正式啟用，新研究（Study）應明確綁定 v006；v005 已停止接受新 Study，治理狀態為 Superseded。原 v005 Package、發布核准及既有 Study 保持原地與原版本綁定；本次只新增 v006 Release Record（發布核准紀錄）及更新兩份治理文件。

v006 原 122 個定義、manifest（發布清單）、test report（發布前測試報告）、八份 Policy／Policy Release 與公開策略程式完整保留。原 25 日暖機不足仍會被拒絕；正式啟用不代替 TASK-036 的新暖機準備或原定 v009 Control 管線。TASK-040／041 的版本專屬 skills 尚未建立，TASK-036 仍 Pending，等待既定依賴與 PM 明確重新派工。

## 本次核准與啟用時間

使用者在本次列明三個完整指紋及版本交接的核准詢問中明確回覆：

> 核准 v006: ochowei@gmail.com

核准者為 `ochowei@gmail.com`。收到回覆後即刻讀取 UTC 時鐘，記錄本次核准時間 `2026-10-02T03:25:11Z`（台北時間 11:25:11）；實際新增 Release 後立即記錄啟用時間 `2026-10-02T03:30:52Z`（台北時間 11:30:52）。核准時間與啟用時間分別保存，沒有挪用 v005 或外部人造示範的核准。

原始回覆、指紋、範圍及核准記錄時間來源保存於 [本次核准紀錄](../approvals/TASK-039-v006-20261002.json)，SHA-256 數位指紋為 `e8711418637dc4257eb91500c9dea462ff5d11bd9b3626eabbe84f40e5708bd3`；PM 在正式驗收時重新核對該原始檔案仍完全相同。

## 最終發布內容

| 內容 | SHA-256 數位指紋 |
| --- | --- |
| Workflow，122 份定義 | `e527578ca62d907d5b1e16f57d5a4c52f0b7cabb9d616970eb2eb2e383f8e7a9` |
| Release manifest | `e87dbb536b95c7b7e3ec9842732cb6d87a6db3fb9238262841cde16ba4880882` |
| 原始 test report，10 項檢查 | `e7028200de3a9ed38b321d666c741234ac7306edf34f66b00dbccc8b211bf8fe` |
| 新增的正式 Release Record | `61d6eeebe58fdd40d6805ca461ccc9a327b9aa153eedd6414a612ddc5ad3594f` |
| `docs/workflow-lifecycle.md` | `7fd49c1bdf7098075be70367cb239ec621aa369c1b505dae5e1a6eec84ae804c` |
| `workflows/README.md` | `f94cba8a70f05187156954b23403c8813b739b0b0ae42c7df9c0b81278ef2b70` |

發布原始檔案：[v006 release.yml](../../workflows/strategy-forward-replication-research--v006/release.yml)、[release-manifest.yml](../../workflows/strategy-forward-replication-research--v006/release-manifest.yml)、[release-test-report.yml](../../workflows/strategy-forward-replication-research--v006/release-test-report.yml)。

## PM 獨立驗收

1. 以 `validate_release_record` 核對正式 Release 格式、完整 manifest 及三個指紋；核准者與核准 UTC 精確符合本次原始人類回覆紀錄。
2. 重新核對 canonical bytes（固定格式的原始內容）及新 Release 指紋；原 122 個定義、manifest、report 仍與核准內容相同。
3. v005 的 102 份 manifest 明列定義、三份發布檔案、八份 Policy／Policy Release、固定 conformance 程式與兩個公開策略引擎均與初始基準相符。只讀公開指定檔案，不遍歷既有 Study 或正式結果庫。
4. 把已審閱的兩份治理完整預覽反向套用提案差異，精確還原啟用前原檔指紋；再逐位元組比較正式治理文件與填入本次核准者、核准 UTC、啟用 UTC 後的預覽，完全一致。只有已核准的版本狀態與交接內容變更，Lifecycle 規則及舊核准紀錄保留。
5. 正式文件記錄 v006 Active、v005 Superseded，核准與啟用 UTC 正確；沒有未填入的占位文字。治理檔案格式及 `git diff --check` 通過。
6. v006 沒有 Study、runtime、evidence 或 authority；本次沒有啟動任何真實 Study 或 Historical Evaluation。

PM 稽核目錄：`/private/tmp/task039-v006-pm-preactivation-20261002-ihwmsejb/`。`pm-active-audit.json` 記錄正式 Release、原始核准及不可變基準核對；`pm-final-governance-audit.json` 記錄兩份治理內容精確相符、最終指紋與台北時間。

TASK-039 沒有重跑完整 pytest；完整 Draft、執行者 RC、PM RC 各 207 passed／212 個 NumPy 警告是 [TASK-038](task-038-v006-release-candidate-acceptance.md) 的發布前證據，原報告保留 RC／`release_record_created=false` 的歷史內容。Active 由有效新增 Release 證明，正式啟用階段使用 Active 驗證路徑，沒有使用會拒絕正式 Release 的 RC checker。

## 交付與後續

正式啟用前的草案、七項隔離示範及首次示範腳本預期錯誤的真實失敗紀錄，都保留於 [啟用前審閱](task-039-v006-preactivation-review.md) 與執行者外部目錄；沒有把合成核准當作本次核准。

執行者已完成 [正式交接](/private/tmp/task039-v006-activation-prep-20261002-pmwkjzaf/formal-publication/handoff.md) 並停止所有編輯，維持 Doing 交 PM 驗收。交接 SHA-256：`ed4012ce4374154abcf88f5f8d7e1b70d7fe0372fa2f461ccad07af34773b60c`；[正式命令索引](/private/tmp/task039-v006-activation-prep-20261002-pmwkjzaf/formal-publication/command-ledger.json) SHA-256：`ebb25be6d5ce62f1a14eb82337dd07e5a20cf0dbb02c05bd869d65208886eb9d`；最終指紋檔案 SHA-256：`13890217ad61b81e200e3cc378f69a43f7e2ad7bfce9d13cb55eb8573d85a1ab`。PM 逐項確認九個正式命令均退出碼 0，實際日誌與索引中的指紋完全相符。

外部 `release-publication.json` 是落檔後、初次驗證前保存的時間紀錄，因此保留當時等待驗證的字樣；最終成功由正式 Active 檢查、最後指紋檔案及 PM 獨立驗收證明，沒有覆寫歷史紀錄。

全部驗收條件符合，由 PM 將 TASK-039 移到 Done。下一項為 TASK-040 的三份 v006 Development、盲檢討、成果卡專用 skills；TASK-041 的評估 skill 另行分派。本次沒有 commit，也未建立 TASK-036 Study。
