# TASK-040：v006 開發、盲檢討與成果卡 skills 驗收

- 驗收日期：2026-10-02
- 驗收角色：專案管理者
- 執行者：`/root/task_040_v006_skills_developer`，固定 study 開發者。
- 獨立審閱者：`/root/task040_skills_independent_review`，固定 study 開發者。
- 結論：驗收通過，TASK-040 由 PM 從 Doing 移到 Done。

## 交付與驗收依據

三個新技能各有 `SKILL.md` 與 `agents/openai.yaml`，共六個新增檔案。指引以 Active v006 的實際 CLI、Schema（檔案必須包含的結構）、公開操作與檢查程式為準。舊 v004／v005 skills 原地保留；沒有額外腳本或未使用的資源目錄，自動發現維持預設。

| 驗收要求 | PM 審閱結果與實際依據 |
| --- | --- |
| 建立前完整檢查、派工及版本綁定 | build 技能明列完整研究輸入、真實派工與 identity。全域參數置於子命令前、create 不帶 Study 位置參數、resume 接續原 operation，與 `operations/cli.py`、`operations/service.py` 及 assignment／計畫 Schema 一致。 |
| v006 暖機及原生合成 guard | 包含最長指標就緒邊界，含當日 SMA50 需49個先前交易日。新 Study 使用唯一外部 implementation contract；原生報告綁定真實來源、引擎、完整契約及指紋，不能用成功旗標、替代引擎或重新簽造報告繞過。對照 `reference/synthetic-diagnostics.md`、`operations/legacy_checks.py` 與 `validator/synthetic_report.py`。 |
| 唯一 Trial、完整凍結及多資產 | 固定候選／唯一 Trial 派工不擴張；保留其他已登記最大 Trial 路徑、完整 family 與只追加 registry。單資產與1–16資產清單擇一、固定可得時間、日期對齊及隔離執行。凍結還要完整綁定、選擇、來源及 snapshot，不能把局部 eligible 當成全部完成。 |
| 盲檢討界線 | 第一份 Study 檔案前固定白名單，先核 reference，再讀指定設計與 Development publication；不查 status、events、operations、runtime 或正式結果。缺證據標示無法取得，不能推定未執行。 |
| 成果卡效力與追加 | 分清正式門檻、研究目標、證據有效性、凍結資格及實際狀態。已登記 target 失敗雖不是 gate fail，仍阻止 Trial 凍結資格；與 `validator/qualification.py` 一致。runtime 只允許可信交接精確定位的 Development manifest，不列舉其他操作；寫檔須明確指定，只新增或追加並核對原文前綴。 |

成果卡的 runtime 例外只准精確 manifest；不能直接用 `operations.runtime_manifest.load_runtime_manifest` 擴張讀取，該函式會另讀 request／plan。只在已授權白名單內核對可重建或有可信來源的指紋，無法核對的部分需列為限制。

## 實際檢查及其範圍

- 執行者及 PM 都逐份執行 skill-creator 的 `quick_validate.py`；安裝後 PM 三份均 exit 0、`Skill is valid!`。這只證明技能格式，不代替契約審閱。
- PM 核對六個安裝檔案與已審閱草稿 bytes 完全相同；所有文件連結存在，UI YAML 可解析、說明長度44／44／40字元，預設提示均包含正確技能名稱。
- PM 的139項檔案指紋比對通過：八個 v004／v005 技能目錄共12檔，以及 v006 定義、發布檔與兩份治理文件共127檔均不變。另重驗 v005 102個定義、三份發布檔、八份 Policy、公用候選與 v009 引擎基準，全部相符。
- 以 `validate_release_record` 重驗正式 v006 Release；不把已啟用 Release 當成 RC 重新跑候選 checker。
- 獨立審閱只使用技能與公開定義，處理三個假設請求。暖機不足時停在 create 前；沒有另給 Trial IDs 時，由事前登記的 candidate IDs 精確定位 publication；gates 過但 target 未達及 provenance unknown 時，不宣稱可凍結或已凍結。未發現造成錯誤操作或越界的明確問題。
- 本次沒有執行真實 Study、runner、Study Lifecycle、Historical Evaluation 或完整 pytest，未讀正式結果，未 commit。

## 最終技能指紋

| 技能 | SKILL.md SHA-256 | agents/openai.yaml SHA-256 |
| --- | --- | --- |
| `build-strategy-study-v006` | `868da0b5e0367c274df92c8986487b1678409006d3a55d19cd4ae2123a8bc2b9` | `29d062bfe9a6ac7da44b6abb3f8cf62f394fbd09a59f3c2125cc3005577660d9` |
| `blind-review-strategy-study-v006` | `e6fb3e5e8eaa29a632a9d2899568a5cfc831fa5b1660455ef15143badc7d2c14` | `c3405ef8e0b50324cc6d7a962370cb8f923e0071425319835627da74e3369599` |
| `study-development-note-authoring-v006` | `0cbc398124ada8074bc3e4b0e38ccda56bfb353e34186287bff277b410051b00` | `6b601cd75c53312c86d491603e748494d3e26a110c29064d421bb82374aabc97` |

## 有效發布及接續

- `workflow_digest`：`e527578ca62d907d5b1e16f57d5a4c52f0b7cabb9d616970eb2eb2e383f8e7a9`
- `release_manifest_sha256`：`e87dbb536b95c7b7e3ec9842732cb6d87a6db3fb9238262841cde16ba4880882`
- `release_test_report_sha256`：`e7028200de3a9ed38b321d666c741234ac7306edf34f66b00dbccc8b211bf8fe`
- 正式 Release SHA-256：`61d6eeebe58fdd40d6805ca461ccc9a327b9aa153eedd6414a612ddc5ad3594f`

TASK-039 與 TASK-040 已 Done，TASK-036 恢復 Development 的前置條件已齊備；需另作符合 v006 的明確重新派工，仍須通過完整建立前檢查，不能借用 workflow 示範成果。TASK-041 仍 TODO，屬正式歷史評估技能準備，不是 TASK-036 Development 的前置條件。本次不啟動這兩項任務。

外部原始材料：

- [執行者逐項契約與安裝交接](/var/folders/w4/jth3symj3q92qfklnhw_4tx80000gn/T/task040-v006-skills-20261002-u9jue406/contract-review.md)
- [PM技能與保護指紋核對](/var/folders/w4/jth3symj3q92qfklnhw_4tx80000gn/T/task040-pm-fbpefknc/pm-skill-audit.json)
- [PM正式Release核對](/var/folders/w4/jth3symj3q92qfklnhw_4tx80000gn/T/task040-pm-fbpefknc/pm-active-audit.json)
