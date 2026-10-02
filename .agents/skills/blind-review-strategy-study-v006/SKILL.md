---
name: blind-review-strategy-study-v006
description: 對明確指定的 strategy-forward-replication-research--v006 單一 Study 做盲檢討；只使用研究設計、程式與 Development candidate／baseline evidence，不讀正式 Evaluation、Terminal 或 Study 狀態。
---

# v006 Study 盲檢討

固定 **study 開發者**，只處理明確指定的一個 v006 Study，先遵守 `AGENTS.md`。其他角色不自行切換；不得挑選其他 Study、修改研究或重跑 runner。

## 在任何 Study 讀取前設定邊界

先從目前對話及指派者提供的接觸說明判斷：是否看過正式 Historical Evaluation 資料、輸出或結果，包括績效、fold、gate 或 Terminal outcome。已曝光就停止盲檢討；接觸不明先釐清，在此之前不讀 evidence。只知道日期、階段或 digest 不算績效結果曝光，但此前看過流程狀態仍須揭露，不能宣稱對 workflow state 全盲。

**先固定以下白名單，再開任何 Study 檔案。** 不得用「先查有沒有正式結果」來確認盲性，不跑 `status`、`validate`、完整 projection（重建事件形成的研究狀態）、Git history、資料夾全域搜尋或事件列舉。由指定 Study ID 定位 `workflows/strategy-forward-replication-research--v006/studies/<study-id>/`，以 preregistration 的已登記 Trial 身分或派工明列 Trial IDs 開啟精確路徑；不要掃描整個 Study 找可用檔案。

## Development-only 白名單

| 可讀檔案 | 用途與限制 |
| --- | --- |
| `manifests/workflow-reference.yml` | **首先讀它**；在 Source Bundle／evidence 前核對真實 v006 Package、release manifest、resolver version 與 Workflow／manifest／Policy digests。 |
| `manifests/preregistration.yml`、`manifests/source-bundle.yml` | 只取研究設計與固定來源；Source Bundle 明列且 bytes digest 相符的程式、設定可讀，不能跟讀受限路徑或價格。 |
| `evidence/trials/<trial-id>/publication.yml` | 核對 Study／Trial、Source Bundle、preregistration、candidate／baseline／inputs、envelope 指紋；多資產另核對 data_assets_digest。 |
| publication 明列的 `inputs.yml`、`candidate.yml`、`baseline.yml` | 必須是同一 Trial 的 Development-only artifact；符合 development evidence／envelope Schema，stage=development。只看 inputs 的資料來源、期間、角色及指紋 metadata，不開原始 CSV。 |
| `evidence/provenance.yml`、`evidence/selection.yml` | 只在資格判讀需要時讀取；核對來源、clean／contaminated／unknown、既定選擇次序與其引用，不據此推論正式評估或凍結狀態。 |

在讀取每個白名單路徑與引用前，檢查詞面、repository 內實際解析位置與符號連結；穿越、解析到受限目錄、其他 Study、非 Development artifact 或版本／digest 不符立即停止。白名單中的檔案提到其他路徑不會擴大白名單。若來源混入正式結果，停止並揭露曝光，不能忽略後標記 clean。

依 [操作契約](../../../workflows/strategy-forward-replication-research--v006/reference/operations.md)、[reference 契約](../../../workflows/strategy-forward-replication-research--v006/reference/workflow-reference.md)，確認 reference 的 `workflow_package_path` 為真實 v006 Package；核對 `release.yml`、實體 `release-manifest.yml` 與 Policy releases，不用 Study 內 Workflow 副本。這只證明允許檔案與綁定的 Package 相符，不證明 event-chain binding、完整狀態或實際 freeze。

## 真實契約與資格判讀

- 依 `schemas/development-publication.schema.yml`、`development-evidence.schema.yml`、`development-envelope.schema.yml` 核對格式與所有 exact digests；不能只憑 artifact 自稱 pass。candidate／baseline 缺任一臂或 envelope／publication 綁定不足，就無法形成完整比較。
- 參考 [v006 原生合成診斷](../../../workflows/strategy-forward-replication-research--v006/reference/synthetic-diagnostics.md) 檢查固定來源中的指標及暖機契約；SMA50 含當日收盤需49個先前 sessions，regime 必須使用真實 Close 及完整視窗。可以指出實作／登記不一致，不能呼叫 prepare、precreate、synthetic diagnostics、runner 或讀 prepare／operation 報告補足盲檢討。
- 依 [多資產資料契約](../../../workflows/strategy-forward-replication-research--v006/reference/multi-asset-input.md) 分辨單資產與1–16資產清單，不能混用。核對唯一 trade、reference 資產、逐檔指紋、清單指紋與 publication／inputs 引用；參考資產不是交易標的，不開 CSV。
- 按 preregistration 的完整候選 family 核對每個允許的 Trial publication。找不到 publication／必要 artifact 就標示 evidence unavailable（此範圍內無法取得證據），不推定未執行、未登錄或通過；不得查 events 補齊 registry。
- 分開重算正式 gates（必要績效門檻）、research targets（事先登記的研究目標）、證據有效性及 Trial-level freeze eligibility。target-only 失敗不等於 formal gate fail，但 v006 的 eligibility 同時要求 targets 成立與有交易。合法績效 fail 仍可能是有效 evidence。
- 完整凍結資格還需要完整 family／registry、已登記選擇／同分次序、至多一個候選、不同且較簡單 baseline、verified-clean provenance、來源／資料／Workflow／Policy 綁定及 floors／drift 規則。若白名單無法證明完整 registry 或任一必要事實，寫「尚不能判斷」；不能讀狀態補足。qualification 判讀不證明實際 candidate freeze 已完成。

## 禁止範圍與輸出

不開啟、搜尋、列舉、雜湊、複製或引用 `historical-evaluation-artifacts/`、任何 Historical Evaluation／Terminal evidence、quarantine 或評估價格；不讀 `study.yml`、`events/`、`journals/`、`operations/`、`runtime/`、authority checkpoint 或恢復資料。不進入 `.super-admin/`、非共享 `.project-manager/` 等受限目錄。不執行 runner、Lifecycle、freeze-readiness 或任何寫入／狀態查詢。

繁體中文回覆 Study ID、reference 核對、盲性與既有曝光、逐 Trial 的綁定／有效性／gates／targets／資格、已確認問題及影響、尚不能判斷事項與下一輪可否證建議。明確說明未讀正式結果與狀態、未核對完整事件鏈；已有狀態知識時如實揭露。預設只在對話輸出，不寫 Study、evidence 或事件。
