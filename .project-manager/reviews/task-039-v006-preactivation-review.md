# TASK-039：v006 啟用前審閱與核准內容

- 日期：2026-10-02（Asia/Taipei）
- 審閱角色：專案管理者
- 執行者：`/root/task_038_v006_executor`，維持 workflow 執行者角色，接續 TASK-039。
- 狀態：啟用前審閱及本次新核准已完成；正式落檔與 PM 驗收均通過，TASK-039 已 Done。以下保留核准前草案與審閱過程；目前正式結果見末節。

## 核准後的實際影響

本次啟用的是已由 TASK-038 驗收的 v006：補足長期趨勢／均線條件的人造案例、最長暖機檢查、建立研究（Study）前的報告與來源核對，以及完整流程相容性。研究門檻、成本、風控、資料區間、一次正式評估及 1–16 資產能力沿用原規則。

取得本次明確核准後，由 workflow 執行者新增 v006 根層的 `release.yml`，驗證其綁定下列三個指紋；再記錄 v006 Active、v005 Superseded（停止接受新 Study）。v005 原 Package、核准紀錄及既有 Study 維持原地與原版本綁定。

本任務的具體變更為：

1. 新增 `workflows/strategy-forward-replication-research--v006/release.yml`，記錄本次真實核准者、核准時間及三個指紋。
2. 更新 `docs/workflow-lifecycle.md`，記錄實際啟用／取代時間與原因，保留 Lifecycle 的既定規則。
3. 更新 `workflows/README.md`，將供新 Study 使用的版本標為 v006，並說明 v005 的既有 Study 繼續依原綁定處理。

已驗收的 Workflow 定義、manifest、test report 及 Policy 原始內容保持固定。test report 的 RC／`release_record_created=false` 是發布前測試時的紀錄；正式啟用由新 Release Record 證明。TASK-040／041 的 skills 與 TASK-036 真實 Study 留在各自任務。

## 本次核准所綁定的最終內容

| 內容 | SHA-256 數位指紋 |
| --- | --- |
| Workflow，122 個發布定義 | `e527578ca62d907d5b1e16f57d5a4c52f0b7cabb9d616970eb2eb2e383f8e7a9` |
| Release manifest | `e87dbb536b95c7b7e3ec9842732cb6d87a6db3fb9238262841cde16ba4880882` |
| 最終 test report，10 項檢查 | `e7028200de3a9ed38b321d666c741234ac7306edf34f66b00dbccc8b211bf8fe` |

可審閱的原始檔案：

- [v006 Package 與操作規則](../../workflows/strategy-forward-replication-research--v006/README.md)
- [release-manifest.yml](../../workflows/strategy-forward-replication-research--v006/release-manifest.yml)
- [release-test-report.yml](../../workflows/strategy-forward-replication-research--v006/release-test-report.yml)
- [TASK-038 完整驗收與限制](task-038-v006-release-candidate-acceptance.md)

## Release Record 草案

以下是審閱用的內容模板，未寫入正式 Package。`approved_by` 與 `approved_at` 必須等本次真實核准後填入；目前的 null（尚未填入）會被正式 Schema（資料格式規範）拒絕，不能拿來作為有效 Release。

```yaml
schema_version: 1
workflow: strategy-forward-replication-research
workflow_version: v006
workflow_digest: e527578ca62d907d5b1e16f57d5a4c52f0b7cabb9d616970eb2eb2e383f8e7a9
release_manifest_digest: e87dbb536b95c7b7e3ec9842732cb6d87a6db3fb9238262841cde16ba4880882
test_report_path: release-test-report.yml
test_report_digest: e7028200de3a9ed38b321d666c741234ac7306edf34f66b00dbccc8b211bf8fe
approved_by: null
approved_at: null
```

正式落檔採只新增方式，已有 `release.yml` 就停止，避免覆寫。落檔後以 `validate_release_record` 檢查完整定義、manifest、test report 與核准內容，再檢查固定 Policy 及治理文件。Active 有自己的驗證路徑：RC checker 會拒絕已存在的正式 Release，因此正式啟用後不以該拒絕誤判發布失敗。

## 啟用前檢查

PM 已於 2026-10-02 重新獨立確認：

- 122 個發布定義、manifest、report 格式與原始內容，以及最終三個指紋與 TASK-038 交付完全相符。
- report 的 10 項檢查均通過；完整 Draft、執行者 RC、PM RC 各 207 passed、212 個 NumPy 警告，原結果與限制保留，未重跑完整 suite。
- v005 的 102 份定義、三份發布檔、八份 Policy／Policy Release、固定 conformance 檔案與兩個公開策略引擎均與原基準相符。
- v006 根層沒有正式 Release、Study、runtime、evidence 或 authority。
- 實際治理文件仍為 v005 Active。

PM 本次稽核材料：`/private/tmp/task039-v006-pm-preactivation-20261002-ihwmsejb/`，包含目前 RC、保護基準、治理原檔指紋與 `pm-proposal-review.json`。

執行者的具體審閱材料如下，全部為專案外的待核准草案，尚未套用：

- [核准審閱卡](/private/tmp/task039-v006-activation-prep-20261002-pmwkjzaf/release-record.review.md)
- [Release Record 模板](/private/tmp/task039-v006-activation-prep-20261002-pmwkjzaf/release-record.template.yml)，SHA-256：`c23be0f4babf1931ab85026fed76a53866473318f03ca0b69fed8ccfa99e14d7`。
- [兩份治理文件的具體差異](/private/tmp/task039-v006-activation-prep-20261002-pmwkjzaf/governance-proposal.patch)，SHA-256：`30dfa4608d02a6f38bd73dd78e9b33e46b112772b9edd64798a5d3d625c37dd1`。
- [Lifecycle 完整預覽](/private/tmp/task039-v006-activation-prep-20261002-pmwkjzaf/proposals/docs/workflow-lifecycle.md) 與 [Workflow 索引完整預覽](/private/tmp/task039-v006-activation-prep-20261002-pmwkjzaf/proposals/workflows/README.md)。本次核准者、核准 UTC 與實際啟用 UTC 等待真實紀錄，預覽中的占位文字不代表已啟用。
- [核准後唯讀 Active 驗證方式](/private/tmp/task039-v006-activation-prep-20261002-pmwkjzaf/verify_active.py)。

PM 已核對模板的九個欄位、兩個待核准 null 及三個固定指紋；治理提案只涉及預定的兩份檔案，`git apply --check` 退出碼 0，原治理文件仍未變動。七項外部合成示範的真實結果符合預期：null 模板拒絕、有效格式的 Active 正例、Active 副本拒絕 RC checker、相同內容不寫入且 inode／指紋不變、不同內容拒覆寫、錯 manifest／report 指紋拒絕。這些示範只使用人造核准與外部副本，不具正式核准效力；第二輪 log 指紋為 `7ec58a797cf7a95a41b3d041246316f73127a3826b0a09c6d4ad678fb66e25e6`，退出碼 0。

第一輪外部示範腳本錯把「相同內容不寫入」預期為拋出 FileExistsError，實際工具會返回 no-op（未寫入）；真實 exit 1 與 trace 已保留。只修正外部示範的預期，使用全新副本完成上述七項檢查，未修改 Workflow 或降低 guard。正式落檔另有事前停止條件：已有根層 Release 就停止，不嘗試重寫。

## 最後核准條件

[Lifecycle 的 TASK-039 啟用條件](../../docs/workflow-lifecycle.md) 與共享看板 TASK-039 第一項驗收條件要求：獨立 Trusted Approver（實作者以外的核准者）檢視最終內容，針對本版本的三個指紋給出新的明確核准。v005 舊核准不能作為 v006 的核准；Schema 只能檢查格式，真人核准由本次原始回覆佐證。

核准者若同意上述版本與交接內容，請回覆：`核准 v006；核准者：你的姓名或識別`。PM 保存本次核准文字與實際記錄時間，再指派 workflow 執行者正式落檔；沒有收到該核准前維持 RC。

若落檔後核對失敗，保留正式 Release Record 與原始證據，停止後續交接並回報 PM；不得刪除、覆寫 Release 或自行換用其他指紋。治理紀錄與實際狀態須據實記錄，交由 PM 決定後續處理；規則變更另建新版本。

## 本次真實核准紀錄

使用者在本對話中回覆針對上述三個完整指紋及 v006 Active／v005 Superseded 的核准詢問：

> 核准 v006: ochowei@gmail.com

核准者為 `ochowei@gmail.com`；收到回覆後即刻以 UTC 時鐘記錄本次核准時間 `2026-10-02T03:25:11Z`（Asia/Taipei 為 2026-10-02 11:25:11）。這是本次真實回覆所給的身份與時間，不是沿用 v005 或人造示範。

原始核准內容、三個指紋、範圍與記錄時間來源保存在 [TASK-039 核准紀錄](../approvals/TASK-039-v006-20261002.json)。PM 在核准後再次重驗 RC 三個指紋與全部保護基準，仍完整相符；授權 workflow 執行者依本次核准正式新增 Release Record 與套用已審閱的治理交接。正式落檔及 PM 最終驗收另依實際結果記錄。

## 正式落檔與驗收結果

v006 已於 UTC `2026-10-02T03:30:52Z`（台北 11:30:52）正式啟用，v005 停止接受新 Study；兩份治理文件精確符合本次核准提案。正式 Release 指紋為 `61d6eeebe58fdd40d6805ca461ccc9a327b9aa153eedd6414a612ddc5ad3594f`，三個核准指紋與全部保護基準保持原樣。九項正式命令及 PM 的核准／Active／治理內容獨立驗收均通過，TASK-039 移至 Done；完整證據見 [正式啟用驗收](task-039-v006-activation-acceptance.md)。
