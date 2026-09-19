---
name: study-development-note-authoring-v002
description: 為 strategy-forward-replication-research--v002 的單一 Study 撰寫 300–600 字 Development 成果卡，使用逐 Trial candidate／baseline 證據並區分 gates、targets、證據有效性與凍結資格。僅超級管理者或 study 開發者使用，不讀正式結果，不適用 v001。
---

# v002 Development 成果卡

成果卡是給人閱讀的補充筆記，不是正式 evidence、事件或結果。只整理使用者指定的一個 v002 Study，不自行跨 Study 比較。角色須為 **超級管理者** 或 **study 開發者**，不得自行切換；目前角色不符就停止使用技能。

先讀 AGENTS.md 及本技能的 [成果卡模板](study-outcome-note-template.md)。若本 task 已接觸目標 Study 的正式 Evaluation 或帶 outcome 的 Terminal 內容，停止，請在未帶入結果的新 task 撰寫。不能從未輸出 evidence 推定未看過結果；曝光資訊不明時先釐清。

## 唯讀檢查與資料範圍

```bash
python .agents/skills/study-development-note-authoring-v002/scripts/check_development.py <study-id-or-path> --repository-root <repo> --role 'study 開發者'
```

超級管理者改傳對應 role；工具不證明呼叫者身分。它只接受 v002 studies 的直接目錄，拒絕 symlink／逃逸。已確認曝光可用 `--outcome-exposed` 或個別曝光旗標。非零退出即停止；零退出只表示範圍可讀，另檢查每個 Trial 的 evidence_validity。

工具透過 v002 validator 重算 publication 綁定的 candidate／baseline，沒有讀取事件、authority 或 projection，不能證明 Trial 已登錄或 candidate 已凍結。不要改用 v001 工具、完整 status／validate、writer、runner 或臨時重跑。

只按需要讀取：

- 指定 Study manifests 的 preregistration、source-bundle、prepare-report settings，以及存在的研究規格與 snapshot metadata。
- 預先登記 Trial 的 `evidence/trials/<trial-id>/{publication,candidate,baseline,inputs}.yml`；先有合法驗證結果才可填數值。
- Development authorization、provenance、selection，僅作 Development 補充，不反推正式事件完成。
- Source Bundle／prepare settings 明確綁定且 digest 一致的 `research/<id>/` 研究規格與 Development 程式，以及 `src/`、`tests/` 中直接相關的程式／測試。先檢查路徑與 symlink；不把 manifest 任意路徑當授權。
- 使用者明確提供、確定為 Development-only 且聲明未讀正式結果的盲檢討筆記；內容範圍不明就不讀。

不得開啟、搜尋、雜湊、複製或引用 `historical-evaluation-artifacts/` 或任何位置的正式 Evaluation／Terminal 結果。不讀 study.yml、events、journals、operations/runtime、Study／research README、全域搜尋或 Git 歷史。不從 /tmp、相似研究、full／quarantine／Evaluation 價格、網路或 connector 補值。

## 成果卡判定

按預先登記 family 逐 Trial 判定，不挑最好看的 Trial 當整體結果：

- `complete`：必要 candidate／baseline 的 base／stress 證據完整、可驗證，formal gates 通過。這不代表 research targets 通過、候選合格或已凍結。
- `failed`：合法且完整的 evidence 顯示 formal gates 失敗。
- `partial`：部分已登記 Trial／情境可驗證，其餘尚未完成或不可用；分別列明，不能讓成功者遮蓋缺口。
- `evidence-unavailable`：必要 evidence 缺失、無法讀取或 validator 拒絕，且沒有可驗證的完整 Trial。停止其數值與 gate 分析，保留已確認的缺件及影響。
- `indeterminate`：允許資料不足以判定執行情況或上述狀態，不猜測。

無交易的合法 evidence 可填交易數 0，其餘無法估計者寫「不可估計」，不得當成缺檔，也不得捏造 PF／bootstrap。正式 gate 通過、target 失敗時，成果卡可為 complete，但必須另寫 target failed、候選不合格；不得把 target 加入 formal failed_gates。

`candidate_freeze_status` 預設「尚不能判斷」；eligibility 只表示資格，不等於凍結事件已完成。Provenance 若僅有陳述而未完成事件驗證，明示「文件記載，未驗證事件」。缺 evidence 不代表未執行，不代表沒有接觸真實資料。

## 撰寫與保存

正文約 300–600 字，表格與來源不計字數；最多 3 個發現、2 個限制、1 個下一輪主要變更。分清「已確認」、「可能原因」、「尚不能判斷」。每項數值指出 Trial 與 candidate／baseline；只填 Development/base、Development/stress。下一輪提出事前成功與否證條件；缺證據時優先修復產製／驗證問題，不擅改策略參數或重跑原 Study。

預設直接在對話輸出，不建立檔案。使用者明確要求寫檔且提供精確目標路徑時，確認路徑不是 symlink／受限目錄或正式 artifact；新檔才建立。既有檔只有確定是 Development-only 成果卡集合時，保留原文並 append 分隔線、日期、Study ID 及新卡片，不覆寫或重排。用途不明則請使用者提供新路徑。不可修改 workflow、策略、測試、manifests、evidence、events、journals、authority 或正式結果。

結尾附實際使用的允許來源及讀取限制，使用繁體中文，不宣稱完整 Study 驗證或已知正式結果。
