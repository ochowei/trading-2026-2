---
name: blind-review-strategy-study-v005
description: 對明確指定的 strategy-forward-replication-research--v005 單一 Study 做盲檢討；限研究設計、程式及 Development candidate／baseline evidence，不讀正式 Evaluation、Terminal 或 Study 狀態資料。
---

# v005 Study 盲檢討

目前角色必須是 **超級管理者** 或 **study 開發者**。只檢討使用者明確指定的一個 v005 Study；不自行挑選或比較 Study，不修改 Study，也不執行或重跑 runner。開始前遵循 repo 的 `AGENTS.md`。

## 先確認盲性與 Study 綁定

在開啟 Study evidence 前，檢查對話已知事實及使用者提供的 outcome exposure 說明。若已看過正式 Historical Evaluation 的資料、輸出或結果（包括績效數值、fold 結果、gate outcome 或 Terminal outcome），停止盲檢討；只知道階段、日期或 digest 不算結果曝光。曝光狀況不明時先釐清，在釐清前不得讀取 Study evidence；不得把已知結果說成盲檢討。

使用者必須指定 Study ID。依 v005 文件確認 Study 位於 `workflows/strategy-forward-replication-research--v005/studies/<study-id>/`，再讀取 `manifests/workflow-reference.yml`。檢查路徑沒有穿越或 symlink escape，且 reference 的 workflow ID／version、package path、release-manifest path、resolver version 及各 digest 符合 v005 schema，並以其綁定的 package、release manifest 與 Policy releases 重算核對。任何缺件、不一致或 digest 漂移都停止並回報。不要用複製在 Study 其他位置的 Workflow 取代 reference。

本 skill 不讀取事件鏈或其他狀態資料，因此只能確認 Study 路徑中的 reference 與目前 v005 package 一致；不得宣稱已驗證 event-chain binding、完整 Study 狀態或正式階段。操作細節依 [v005 操作契約](../../../workflows/strategy-forward-replication-research--v005/reference/operations.md)、[Workflow reference 契約](../../../workflows/strategy-forward-replication-research--v005/reference/workflow-reference.md) 及相關 schema。

## Development-only 讀取清單

只讀取以下與指定 Study 綁定的內容，並逐一核對 canonical digest 與引用關係：

- `manifests/workflow-reference.yml`、`manifests/source-bundle.yml`、`manifests/preregistration.yml`，以及 source bundle 明列且 digest 相符的研究程式與設定。
- `evidence/trials/<trial-id>/publication.yml` 引用的 `inputs.yml`、`candidate.yml`、`baseline.yml`。v005 publication 必須綁定 Study ID、Trial ID、source-bundle／preregistration digest，且完整引用 candidate、baseline、inputs；核對 envelope digest 及有多資產時的 `data_assets_digest`。
- 若本次判斷需要，讀取 `evidence/provenance.yml`、`evidence/selection.yml` 作為 Development-to-freeze 的補充證據；不得由它們推論正式 Evaluation 已執行或結果如何。

依 preregistration 的完整 candidate family 逐一檢視可找到的 Trial publication。候選／baseline evidence 必須符合 `development-evidence.schema.yml` 與 `development-envelope.schema.yml`，stage 為 `development`。遵守 v005 單資產或 `data_assets` 契約及固定資料角色；只看 Development inputs 中的資料來源、期間與 digest metadata，不開啟原始 CSV。Development evidence 的 `fail` disposition 仍可是一份有效研究證據，須分開判斷 evidence 完整性與策略表現。

找不到某 Trial 的 publication 或必要 artifact 時，只標示該 Trial 的證據 unavailable；不得推定 Trial 未執行、未登錄或成功。依可見資料判斷「按 Development evidence 是否符合凍結資格」，不可宣稱實際 candidate freeze 已完成。

## 禁止讀取與操作

- 不開啟、搜尋、列舉、雜湊、複製或引用 `historical-evaluation-artifacts/`、任何 Historical Evaluation／Terminal evidence、quarantine 或 full Evaluation 資料；即使 Development manifest 提到其路徑也不得跟讀。
- 不讀 `events/`、`journals/`、`operations/`、`runtime/`、`study.yml`、authority checkpoint、Git 歷史或其他狀態／恢復資料；不執行 `status`、`validate`、完整 Study projection、runner、prepare、freeze-readiness 或任何會讀取後續階段／寫入狀態的命令。
- 不進入 `.super-admin/`、`.project-manager/` 的非共享內容或受限路徑。若允許清單中的路徑解析到受限目錄，立即停止。

若證據顯示正式結果已混入 Development inputs 或研究程式，停止並說明曝光範圍；不可試圖忽略、遮蔽或重新標記為 clean。

## 判定與輸出

對每個可檢視 Trial 分開報告 preregistration／inputs 綁定、candidate 與 baseline evidence 完整性、formal gates、research targets 及依 Development evidence 重算的凍結資格。不可把 research target 失敗寫成 formal gate 失敗；Evidence 缺漏寫 unavailable，不推定未執行。標出 digest／binding 不一致與其影響。

以繁體中文輸出：Study ID 與 reference 核對結果、盲性判定、逐 Trial 結論、已確認問題與影響、證據強度及限制、下一輪可否證建議。清楚聲明未讀取正式 Evaluation／Terminal 或狀態資料；預設只在對話回覆，不寫入 Study 或 evidence。
