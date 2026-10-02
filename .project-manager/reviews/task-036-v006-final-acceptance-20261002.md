# TASK-036 v006 最終驗收

日期：2026-10-02  
角色：專案管理者  
Study：`tsm-divergence-sma20-sma50-regime--v002`  
執行者：`/root/task_036_v006_resume`（study 開發者）

## PM 驗收結論

驗收通過。唯一 Development Trial 及 Development-only review／成果卡已完成，未重跑 Trial。本紀錄完成後，TASK-036 由 Doing 移至 Done。候選未達正式門檻且不具凍結資格；這是有效的 Development 研究結果，不代表正式歷史評估結果。

## 派工、建立與恢復

- 本次真實恢復派工記錄：`.project-manager/dispatches/TASK-036-v006-resume-20261002.md`。派工受派者、create plan creator／development actor 與 Development actor 一致為 `/root/task_036_v006_resume`；一個 Study、一個候選、一個 Trial。
- 有效 v006 Release／manifest／test report 及 Workflow／Policy／reference 指紋與 TASK-041 驗收一致；新 worktree／authority 的 prepare／runner binding 均固定於本位置。固定資料 SHA-256=`a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7`；Source Bundle 11/11 檔案 SHA-256 均相符，Bundle digest=`ea1e654018d4e9768f9f964040b6761f6998c466ff0e03e2558a8cc5ff09d7256`。
- 首次 create 在任何 Event 前因 v002 research 計畫與部分 Study 已寫入計畫副本不一致而失敗。原 research 計畫以原 bytes 追加保存；目前 v002 copy 與原 operation 計畫一致。修復後完整 prepare 通過。新舊報告唯一差異為 23 個 `expected_path` 診斷路徑改指同內容的已發布 preregistration；binding、runner cases 與 `native_synthetic` 相同。沒有替換 operation 原報告，使用原 authority／派工經官方 `resume` 接續同一 create operation。
- Create operation ID=`426bf4bf89155a48a99a947c8dbc83fd9c691e8af92dbbcea2010f65b599165f`；三個 Event 為 `study-created`、`preregistration-recorded`、`development-started`。唯一 Development operation ID=`e0c3add94c7882c49eaffc164e75b0c58d54fbf47a0cccee7261e51e907ea473`，狀態 completed。

## 固定研究設計與 Development 證據

Candidate 是訊號日 SMA(20)>SMA(50) 的唯一增加條件，最長指標就緒／fold 暖機及 required history 為 49 個先前交易日；Control 直接使用未修改的 v009 `DEFAULT_SPEC`，暖機為 25 日。兩臂共用 2013-01-01 至 2013-12-31 暖機資料，Development 訊號區間為 2014-01-01 至 2018-12-31。研究 targets 為空（未登記）。Candidate engine SHA-256=`401cc9f72db9b28b2ad5ef4d79abf3f8d00a26b3fc75d0c9dc588ced767c6b8e`；v009 Control SHA-256=`f3163c9b92046d0397ce1daf0cfb320a302c9e994875a4be0e93057a83cef7c4`。

PM 重新核對 publication 指向的 inputs／candidate／baseline 檔案 digest；均相符。兩臂 evidence 為 `stage=development`、`network_access_during_run=false`，分別有 12／24 筆交易。inputs 固定單一 TSM 資料 digest，runtime manifest 指向同一 Development request／output、`execution_workspace=temporary`，output digest 相符。Candidate 與 Control evidence、publication／inputs／Source Bundle／preregistration bindings 及 envelope digest 齊全；worker 的 Schema 與 raw-trade gate 重算通過，PM 也核對發佈檔 SHA 及 gate 結果。

| 手臂 | Base | Stress | 正式 Development gates |
| --- | --- | --- | --- |
| Candidate | 12 筆；報酬 10.9982%；PF 4.6843；最大回撤 1.9994% | 12 筆；報酬 8.2938%；PF 3.6248；最大回撤 1.9999% | 12/13 通過；唯一失敗為 `completed_trades`：12 < 20。其餘 12 項均通過，包括最大已實現損失、bootstrap／LOO stress 門檻及 5 個交易年份。 |
| Control | 24 筆；報酬 33.6761%；PF 5.0364；最大回撤 1.9998% | 24 筆；報酬 26.5232%；PF 4.2042；最大回撤 2.1193% | 13/13 通過，包括至少 20 筆交易與所有 base／stress 門檻。 |

Candidate 與 Control 的 Development evidence validity 都是 `valid`。本次是固定期間的 Development 比較；不把它表述成正式 Historical Evaluation 結果。Control 數值較高是本次 Development 觀察，不作樣本外推論。

## Provenance、盲檢討與凍結狀態

- Provenance 維持 `provenance-unknown`。目前沒有 `evidence/provenance.yml` 或 `evidence/selection.yml`，不足以證明來源、既有曝光與選擇紀錄達到 `verified-clean`；新 worktree、session 或 Study ID 不改變此結論。
- Candidate trial-level freeze eligibility=`false`，因正式 `completed_trades` gate 失敗。完整 freeze qualification 不成立；selection／provenance 也缺少，無從宣稱完整資格通過。實際 Study marker 為 `current_event=trial-recorded`、`event_count=4`、`candidate_freeze=null`；本次未執行 freeze。
- Development-only review 僅據研究設計、固定來源程式及該 Trial 的 Development evidence。worker 為恢復原 create，於 review 前曾讀取三個 create Events 與 Development status；這違反盲檢討技能「不查 status／events」的讀取邊界。該曝光限於 create／Development workflow state，未讀正式 Evaluation／Terminal 結果或價格 CSV；因此交付必須如實標示為非全狀態盲，不能聲稱 workflow state 全盲。review 的限制已寫入成果卡及交接。
- 未執行 freeze、Historical Evaluation、Terminal、challenge 或 replay；未讀 `historical-evaluation-artifacts/` 或 `.super-admin/`。

## 成果卡

已按使用者指定追加至 `.study-developer/development-note/TSM.md`。追加卡片 600 個字元（含標題及空白；非空白 556）；原有 106,539-byte 內容為完整前綴，SHA-256=`6b2300fe8e7bf8e7e1323f842ac252a968753b4429bcc36ea1f9849d6ebd650d`；最終檔案 107,353 bytes，SHA-256=`21590e4a816657fadb2c0e9fcce78af6e1f99ec77625fc4375d47abfb4ac6fda`。PM 以目前 repository `HEAD` 原檔獨立驗證 prefix bytes 相同。
