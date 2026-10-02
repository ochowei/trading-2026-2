# TASK-041：v006 歷史評估 skill 驗收

- 日期：2026-10-02；驗收角色：專案管理者。
- 執行者：`/root/task_041_v006_evaluation_skill`，固定 workflow 維護者。
- 獨立審閱者：`/root/task041_independent_review`，固定 workflow 維護者。
- 結論：通過，TASK-041 由 PM 移至 Done；依使用者順序接續 TASK-036。

## 實際交付與檢查

新增 `.agents/skills/run-strategy-historical-evaluation-v006/SKILL.md` 與 `agents/openai.yaml`，自動發現維持預設。執行者和 PM 的 skill-creator 格式 checker 均通過；安裝兩檔與已審閱草稿逐一 bytes 相同，UI 格式及技能提示一致。PM 145項保護檔案指紋比對通過：18個既有技能檔案與127個 v006 定義／發布／治理檔案不變。正式 Release Record 重驗有效。

| 契約 | 核對結果 |
| --- | --- |
| 角色、派工、命令 | 限已固定的歷史評估角色、單一已凍結 Study 與明確評估派工；全域參數前置、historical-evaluation 和 resume 參數與 CLI parser 一致，不另要求 Study 人工核准。 |
| 凍結資料 | 單資產 data_digest 核對 CSV bytes；多資產核對排除 data_path／interval_role 後完整清單的 canonical digest、逐檔指紋、唯一 trade、1–16資產與固定 sessions，不能拿單檔 hash 替代總指紋。 |
| 唯一操作與恢復 | reservation／authority／local marker 與原 operation 綁定；仍 started 且任一 marker 已存在即走 unavailable→indeterminate，不宣稱可重讀暫存輸出或重跑。completed event 已完成或可由 journal 恢復後，僅原 operation 接續 terminal。 |
| 保存與效力 | writer 在指定 Study 的專用 artifact 子目錄只新增正式 raw／terminal evidence；同名同內容可確認，不同內容拒絕。隔離暫存的受控輸出與必要的 Study 流程控制資料如實區分，不能自行把含結果日誌保存到其他位置。completed 不等於 outcome pass。 |

對照公開 `operations/cli.py`、`operations/evaluation.py`、`operations/lifecycle.py`、`operations/multi_asset.py`、`writer/service.py`、`validator/canonical_yaml.py`、assignment／evaluation-plan／snapshot Schemas 及 reference。沒有真實 runner、Lifecycle、正式評估或完整 pytest 被執行，未讀正式結果，未 commit。

獨立三個假設情境審閱無實質問題：authority marker 存在而本地 marker 缺失仍拒絕重跑；雙資產只填 TSM hash 時拒絕開始；completed 後不能另建 operation 或把結果日誌存根目錄。

審閱界線紀錄：獨立審閱最初的檔名定位範圍過廣，曾列出其他版本真正 Study 路徑。未開啟任何 Study 內容、未使用那些檔名判斷；PM 指示不得傳回清單，後續審閱限公開五個定義目錄。這是搜尋範圍失誤，不能把此次審閱描述成完全未列出 Study 路徑。

## 最終指紋與交接

- `SKILL.md`：`2461b613b495627ee5e3d9263d2a8c35af18feb402c08b5db348da967c1c45da`
- `agents/openai.yaml`：`18760de155d7ae91cd8532927b49793d557d7c26cd8729ad7115f7c510e36fdf`

- PM 指紋核對：`/var/folders/w4/jth3symj3q92qfklnhw_4tx80000gn/T/task041-pm-mmswlf7m/pm-audit.json`。
- worker 交接：`/var/folders/w4/jth3symj3q92qfklnhw_4tx80000gn/T/task041-v006-skill-rkdf4tqt/handoff.json`。

本次只建立指引，不授權任何 Study 正式評估。TASK-036 另由 study 開發者進行 Development。
