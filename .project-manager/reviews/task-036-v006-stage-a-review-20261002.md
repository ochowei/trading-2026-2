# TASK-036 v006 建立前 Stage A PM 審閱

- 日期：2026-10-02（Asia/Taipei）
- 審閱角色：專案管理者
- 執行者：`/root/task_036_v006_resume`，固定角色 study 開發者
- Study：`tsm-divergence-sma20-sma50-regime--v002`
- 決定：Stage A 通過；僅放行後續唯一 create 與唯一 Development Trial，TASK-036 維持 Doing。

## 審閱依據

完整 worker handoff：`.study-developer/task-036-v006-resume-20261002/stage-a-handoff.md`。PM 使用新的報告及實際來源獨立核對，不把舊 worktree 的 report 改欄位重用。舊暫停 checkpoint 留在 `.project-manager/checkpoints/task-036-v006-precreate-paused-20261002/`；沒有覆寫或搬移。

### Release、worktree 與派工

- 目前 worktree 是 `/Users/william/.codex/worktrees/f260/trading-2026-2`，HEAD=`7e240e9df61d149e4aacc21ee94027d0f3c761fb`，為合併後的 detached worktree。舊 prepare/preflight 綁定 `/Users/william/.codex/worktrees/5aa6/trading-2026-2`，以及舊 authority；新報告則重新綁定 `f260` repo 與 `/Users/william/.codex/worktrees/f260/trading-2026-2/.study-developer/task-036-v006-resume-20261002/authority`。
- `release.yml`、manifest 與 release test report SHA-256 分別為 `61d6eeebe58fdd40d6805ca461ccc9a327b9aa153eedd6414a612ddc5ad3594f`、`e87dbb536b95c7b7e3ec9842732cb6d87a6db3fb9238262841cde16ba4880882`、`e7028200de3a9ed38b321d666c741234ac7306edf34f66b00dbccc8b211bf8fe`，與 TASK-041 PM 驗收相同；v006 Workflow digest=`e527578ca62d907d5b1e16f57d5a4c52f0b7cabb9d616970eb2eb2e383f8e7a9`、Policy digest=`c86066b33119366a3172f475ff75f8813ba4b7545571894edfe581afabe32215`、本次 reference digest=`cfe747174027f22b45f6c699cd1675753abedca2a71ed6035cf7626064e906f1`。TASK-041 驗收已重驗有效 Release，當前 Release 檔案 bytes 與其紀錄相同；worker 本次也重新跑 release record、manifest 與 reference resolver 驗證。
- 恢復原文已另存於 PM 派工紀錄及 `.study-developer/assignments/TASK-036-v006-resume-20261002.yml`。該 assignment assignee、create plan 的 `creator`／`development_actor`、development plan 的 `actor` 均為 `/root/task_036_v006_resume`；三份新 plan 通過對應 Schema。初次 v006 assignment 與原 create/development plan 保留。

### 資料、候選與 Control

- 固定 TSM CSV 為 `research/market-data/yahoo/TSM-warmup-development--sha256-a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7.csv`；SHA-256=`a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7`，1,510 筆、日期 2013-01-02 至 2018-12-31。PM 只核對 SHA、標頭和 Date 欄：日期遞增且無重複；沒有把真實價格送進 preflight 或 prepare。固定用途為 2013 暖機、2014–2018 Development。
- Source Bundle digest=`ea1e654018d4e976f8f964040b6761f6998c466ff0e03e2558a8cc5ff09d7256`；PM 獨立重算 11/11 個列入來源 bytes digest，全部吻合。v002 Candidate engine SHA=`401cc9f72db9b28b2ad5ef4d79abf3f8d00a26b3fc75d0c9dc588ced767c6b8e`；未修改 v009 Control engine SHA=`f3163c9b92046d0397ce1daf0cfb320a302c9e994875a4be0e93057a83cef7c4`。
- 正式 Development runner `research/tsm-divergence-sma20-sma50-regime--v002/run_development.py` 明確使用 `control_engine.DEFAULT_SPEC` 執行 v009 Control，Candidate 則由 Candidate engine 的 `DEFAULT_SPEC` 執行；沒有以 Candidate `BASELINE_SPEC` 取代正式 Control。Study 設定只包含訊號日 SMA(20)>SMA(50) 濾網及允許的候選暖機修正；owner=`ochowei@gmail.com`、operator=`operator A`。13 個 Development gates 已固定，research targets 為空。
- `.study-developer/task-036-v006-resume-20261002/candidate-source.diff` SHA-256=`098bac59e138a7c74d69c6dbceef45d6a651ef7ef6db12bcfdd370a58a3a410d`。PM 審閱兩組 unified diff：v002 對 v009 新增當日 Close SMA20/SMA50、只通過 SMA20 嚴格高於 SMA50 的原始訊號；候選暖機由25改49且 required-history 包含49。v002 對既有 v001 的程式差異僅為相同的25→49暖機／required-history修正及註解。其他訊號、門檻、成本、持有、風險、進出場邏輯不變，符合本次授權。

### 新位置的 prepare 報告與狀態

| 新報告 | SHA-256 | PM 核對結果 |
| --- | --- | --- |
| `native-precreate.json` | `1e83473ccd9da4193e6c9196546b8a4bcf32732837ed1bf59aaedb30f80c41e1` | `passed`；0 errors、0 warnings；Source Bundle 與完整建立前檢查通過 |
| `runner-preflight.yml` | `d62e42ac5b3e8427178cc6c313638b6e7fd441464454d3e4af69afc290618cbe` | `passed`；4 個隔離合成案例，不使用固定 TSM CSV |
| `prepare-report.yml` | `256c07fa8dae958825fe8f7b064622337bfbf362db9857bada71572bbbb842d1` | `prepare_checks: passed`；完整 `native_synthetic` 通過，candidate readiness index=49 |
| `prepare-cli-result.json` | `42717c796e6c86281c166232a68b774c23e37907ac8d74fe19ae372c0a6dc772` | CLI `completed`，repo／authority／release／資料與 Source Bundle 綁定新位置 |

Native precreate 與 prepare 的合成診斷覆蓋 SMA regime 上方／下方／相等、未就緒及剛就緒、原訊號、持有／冷卻與退出案例。Runner preflight 的兩個 Historical Evaluation stage 案例屬隔離合成介面檢查，不是正式 Historical Evaluation，也沒有讀取真實 Evaluation evidence。

Runner preflight 與 prepare 各自的 stderr 都出現兩次 NumPy `RuntimeWarning: invalid value encountered in subtract`。報告本身均 passed，native error/warning counters 均為0；handoff 如實保存提醒。這些警告來自合成 preflight／prepare 執行，不是正式資料或研究成績。本次審閱保留其紀錄，判定不阻塞本 Stage A gate。

PM 以精確 Study ID 檢查 v005／v006 正式 studies 路徑，均不存在；新 task authority 路徑亦不存在。Prepare 前後均未建立正式 Study、event 或 operation。指定成果卡 `.study-developer/development-note/TSM.md` 原本已存在、大小106,539 bytes、SHA-256=`6b2300fe8e7bf8e7e1323f842ac252a968753b4429bcc36ea1f9849d6ebd650d`，Stage A 後仍完全相同。另逐 bytes 重核 checkpoint 列出的16項舊檔，全部未變。

Provenance 保持 `provenance-unknown`：既有來源／結果曝露來源與期間尚不完整，不能因新 session、worktree 或 Study ID 改稱 clean。

## Gate 決定

上述建立前檢查、runner preflight、prepare、候選來源差異與身份綁定均符合 TASK-036 固定要求。PM 於本紀錄完成後，明確放行原執行者 `/root/task_036_v006_resume` 依上述新 assignment／plan 執行**唯一** Study `tsm-divergence-sma20-sma50-regime--v002` 的 create 與**唯一** Development Trial。

如果中斷，只恢復已開始的原 operation，不重跑完成 Trial。禁止 freeze、Historical Evaluation、Terminal、challenge、replay 或 commit；完成後 worker 維持 Doing，交 PM 最終驗收。TASK-036 不因本 Stage A 通過而移 Done。
