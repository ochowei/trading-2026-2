---
name: study-development-note-authoring-v006
description: 為明確指定的 strategy-forward-replication-research--v006 單一 Study 撰寫約300–600字 Development 成果卡；只用 Development 證據，區分 gates、研究目標、有效性及凍結資格／狀態，不接觸正式結果。
---

# v006 Development 成果卡

固定 **study 開發者**，只撰寫明確指定的一個 v006 Study；其他角色不自行切換。先遵守 `AGENTS.md`，成果卡是研究說明，不能代替 evidence、派工、blind review、事件、authority 或正式評估。

## 先固定讀取白名單

從本輪對話及指派者提供的接觸事實確認邊界；已看過正式 Evaluation／Terminal outcome 或接觸不明就停止，不用搜尋正式結果來確認是否可以寫。不得以「沒找到結果」推定未執行。以精確路徑讀取，不搜尋其他 Study 或完整事件狀態。

第一個 Study 檔案是 `manifests/workflow-reference.yml`；依 [操作契約](../../../workflows/strategy-forward-replication-research--v006/reference/operations.md)、[reference 契約](../../../workflows/strategy-forward-replication-research--v006/reference/workflow-reference.md) 核對 v006 的真實 repository-relative Package、resolver version、release record／manifest、Workflow／Policy digests，才讀研究或 evidence。檢查詞面與實際解析路徑，穿越、符號連結逃逸、其他 Study 或受限目錄即停止；不用 `runtime/workflow/` 副本。

只讀成果卡需要的：

- `manifests/preregistration.yml`、`manifests/source-bundle.yml`、Source Bundle 明列且 bytes digest 相符的研究程式與設定；已明確提供的 Development 計畫與 Trial inputs，不能跟讀價格 CSV。
- 指定 Trial 的 `evidence/trials/<trial-id>/publication.yml` 及其引用的 `inputs.yml`、`candidate.yml`、`baseline.yml`；必要的 `evidence/provenance.yml`、`evidence/selection.yml`。
- **僅在派工或可信開發交接已明列 Development operation ID 與精確 manifest 路徑時**，可讀該 operation 的 `runtime/runtime-manifest.yml`，核對 stage=development、workflow/source/runner/request/data/output digests、`execution_workspace: temporary`。不能列舉 operations 來找 stage；不能進隔離暫存空間搜尋，也不能跟讀任何正式 artifact 引用。沒有此定位資訊就略過並明列核對限制。

參照 [最小規格](../../../workflows/strategy-forward-replication-research--v006/reference/minimal-executable-study.md)、[多資產契約](../../../workflows/strategy-forward-replication-research--v006/reference/multi-asset-input.md)、[原生合成診斷](../../../workflows/strategy-forward-replication-research--v006/reference/synthetic-diagnostics.md) 與相應 Schema。這些公開契約可解釋暖機、來源與固定門檻；不能呼叫 precreate、prepare、runner、freeze-readiness 或 Lifecycle 來補證據，也不能把合成成功說成正式 Study 成功。

不開啟、搜尋、列舉、雜湊、複製或引用 `historical-evaluation-artifacts/`、任何正式 Evaluation／Terminal evidence、quarantine／評估價格、`study.yml`、events、journals、authority checkpoint、Git history 或其他狀態／恢復資料；不執行 `status`、`validate` 或 projection。對話已知流程資訊如需使用，明確標為交接事實，不據此推論正式結果或聲稱全盲。

## 判讀與寫法

| 要分開的結論 | 根據及實際影響 |
| --- | --- |
| 正式 gates | 由 preregistration 與有效 Development 證據重算必要績效門檻；資料／綁定不足寫尚不能判斷，不能補造通過。 |
| Research targets | 另列登記的研究目標及達成情況；沒登記就寫未登記。target fail 不寫成 formal gate fail，但 v006 仍將它計入 Trial 凍結資格。 |
| Evidence validity | 核對 Development stage、candidate／baseline 兩臂、網路存取false、Schema、preregistration／Source Bundle／資料／Trial 與 publication envelope 引用；不能只信 artifact 自稱 pass。合法績效 fail 或無交易仍可能是有效研究證據，無交易不能補統計值。 |
| 凍結資格 | Trial-level eligible 不等於整體 freeze-ready；還要完整 family／registry、預先排序／同分、至多一個候選、不同且較簡單 baseline、verified-clean provenance、選擇與所有固定綁定／floors／drift 規則。白名單不足以確認時寫尚不能判斷，不能查 events 補齊。 |
| 凍結狀態 | selection、readiness或qualification不能單獨證明已凍結。只有既有可信 Development-only 交接或本輪已授權開發的精確完成佐證才能說已凍結，並指出來源；否則狀態尚不能判斷。成果卡本身不取得狀態讀取權限。 |

資料採單資產 `data_path`／`data_digest` 或1–16筆 `data_assets`，不能混用。保留 asset_id、trade／reference、provider、symbol、各檔指紋、清單指紋、固定期間與可得時間，核對 inputs／publication 及有明確定位時的 runtime binding；不能把 reference 說成交易標的。只看 metadata，不開價格。

以繁體中文白話文寫約 **300–600 字**；最多三個發現、兩個限制與一項下一輪可否證變更。說清楚 candidate／baseline 與 base／stress 結果、差異的單位、正式門檻與研究目標、有效性、完整凍結資格及狀態。標示「已確認」、「可能原因」或「尚不能判斷」；推測不能寫成因果，Development 表現不能寫成正式評估通過。末段列實際 Development-only 來源與讀取限制。

## 輸出與追加

預設直接在對話輸出。**只有使用者明確要求寫檔並指定目標路徑時**，才在角色允許的地方新增或追加；這不授權修改 Study、Workflow、Policy、manifest、evidence、event、authority 或正式結果。目標已存在時只 append（保留全部原文，在末尾新增），先固定原 bytes／指紋，寫後核對原文仍是完整前綴；避免同期寫入，不能安全追加就回報。目標未存在時新增，不用任意預設路徑；不能覆寫舊卡片或補改舊結論。
