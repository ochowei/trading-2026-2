# v004 實作與驗收對照

v004 是 v003 的後繼 Workflow。它保留 v003 的研究規則與 Policy 引用方式，將 Study 對 Workflow、Source Bundle、runner 及執行結果的關係改成「固定引用加 digest 驗證」，避免每個 Study 再保存一份相同的 Workflow package。v003 既有 Study 不遷移、不改寫；只有在 v004 正式 Release 並依 Lifecycle 完成版本切換後，v003 才停止接收新的 Study，不刪除或覆寫既有資料。

## 交付範圍

| 範圍 | 實作與證據 |
| --- | --- |
| Workflow reference | `schemas/workflow-reference.schema.yml`、`validator/workflow_reference.py` 與 Study manifest；限制 repository-relative path、symlink、受限目錄及 Workflow／release／Policy digest 漂移。 |
| Study 低重複 | 建立 Study 時先寫入 `manifests/workflow-reference.yml`；事件、runner report、operation manifest 只保存 reference path／digest，不複製 `runtime/workflow/`。 |
| 暫存執行 | `operations/runtime_manifest.py` 固定記錄 request、Source Bundle、runner、資料與 evidence digest；Development／Historical Evaluation 的重型執行內容只存在隔離暫存 workspace。 |
| 開發至凍結 | 沿用 v003 的 prepare、Development、registry、provenance、readiness、freeze 契約，並由明確 assignment 驅動；不在此階段執行 Historical Evaluation。 |
| blind review | `.agent/skills/blind-review-strategy-study-v004/SKILL.md` 只讀研究設計、程式與 Development candidate／baseline 證據，禁止讀正式 Evaluation、Terminal 或 artifact store。 |
| Historical Evaluation | `.agent/skills/run-strategy-historical-evaluation-v004/SKILL.md` 只對已凍結 Study 執行一次評估，使用暫存 workspace，raw evidence 只新增到外部 artifact store。 |
| Development 成果卡 | `.agent/skills/study-development-note-authoring-v004/SKILL.md` 只整理 Development 證據，不讀正式結果。 |
| 發布邊界 | 產生 `release-manifest.yml` 與 `release-test-report.yml` 作為 Release Candidate 證據；不在本次實作中建立正式 `release.yml`。 |

## 驗收原則

- v004 Package 內不放 Workflow-local `skills/`；所有 v004 skill 都在 repository root 的 `.agent/skills/`。
- 每個 Study 的 reference 必須能重建並驗證相同 Workflow digest；reference 漂移時要在讀取資料前失敗。
- persistent operation runtime 不得出現 `runtime/workflow/`、完整 source copy 或 bars.csv；重新啟動時只能使用相同 request／manifest，不能因局部輸出遺失而自動重跑正式 runner。
- v003 工作樹不得有 diff；v003 的既有 Study、Policy release、歷史 artifact 及治理文件不得被遷移或覆寫。
- 所有測試使用隔離暫存 repository 與合成資料；測試報告記錄完整的 pytest、Ruff、canonical YAML、reference resolver、runtime manifest、crash recovery 與 Release Candidate 驗證結果。
