# TASK-036 v006 Stage A 交接

日期：2026-10-02  
執行角色：study 開發者  
Study：`tsm-divergence-sma20-sma50-regime--v002`  
狀態：Stage A 完成，等待專案管理者審閱；看板維持 Doing。

## 派工、worktree 與範圍

本次是恢復派工，真實原文已存入新的 worker assignment record：

> 請恢復 TASK-036，撤銷先前的暫停指令，依 AGENTS.md 分派 study 開發者執行，完成後由你驗收。

初次 v006 派工紀錄 `.study-developer/assignments/TASK-036-v006.yml` 保留不動；恢復紀錄另存 `.study-developer/assignments/TASK-036-v006-resume-20261002.yml`。本次新 assignment 的 assignee 是 `/root/task_036_v006_resume`。新增的 create plan 中 `creator`、`development_actor` 都是同一 ID；另外準備了恢復版 Development plan，其外層 `actor` 也相同。三個新計畫欄位均通過 Schema 與相等性檢查。

本次 worktree 為 `/Users/william/.codex/worktrees/f260/trading-2026-2`，HEAD=`7e240e9df61d149e4aacc21ee94027d0f3c761fb`。新 authority 綁定 `/Users/william/.codex/worktrees/f260/trading-2026-2/.study-developer/task-036-v006-resume-20261002/authority`。舊報告仍綁定 PM 交接摘要所載的 `5aa6` worktree 與其 authority；舊報告及 PM checkpoint 都未開啟、未修改，也沒有把舊欄位改成新位置。

## Release、reference 與研究輸入

以 v006 的 `validate_release_record`、`validate_release_manifest` 和 reference resolver 實際重算；結果與 PM 交接摘要一致：

- Workflow digest：`e527578ca62d907d5b1e16f57d5a4c52f0b7cabb9d616970eb2eb2e383f8e7a9`
- Release manifest digest：`e87dbb536b95c7b7e3ec9842732cb6d87a6db3fb9238262841cde16ba4880882`
- Policy set digest：`c86066b33119366a3172f475ff75f8813ba4b7545571894edfe581afabe32215`
- Release test report digest：`e7028200de3a9ed38b321d666c741234ac7306edf34f66b00dbccc8b211bf8fe`
- 本次 repository workflow reference digest：`cfe747174027f22b45f6c699cd1675753abedca2a71ed6035cf7626064e906f1`
- Reference 指向 `workflows/strategy-forward-replication-research--v006`，resolver version=`1`。

正式 Study 目錄在準備前及完成後都不存在。固定資料檔為 `research/market-data/yahoo/TSM-warmup-development--sha256-a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7.csv`，SHA-256=`a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7`；檔頭為 `Date,Open,High,Low,Close,Volume`，共 1,510 個交易日，涵蓋 2013-01-02 至 2018-12-31。日期角色仍是 2013 暖機、2014–2018 Development；只檢查固定檔案的指紋與日期中繼資料，沒有把真實資料交給 runner 執行。

研究假說、候選與唯一 Trial 沿用已固定輸入：Candidate=`tsm-mr-v009-sma20-over-sma50-regime-v002`，Trial ID 相同，baseline=`tsm-mr-v009-two-stage-volume-reversal-control-task036-v002`；候選家族只有一個 Candidate，`maximum_trials=1`。Candidate 僅增加訊號日收盤 SMA(20)>SMA(50)，SMA(50) 使用完整 50 日視窗、含當日收盤，需 49 個先前 session 才就緒。持有、風險、成本、其他訊號與門檻未改。身份仍為 owner=`ochowei@gmail.com`、operator=`operator A`；provenance 保持 `provenance-unknown`，沒有因更換 worktree 或 Study ID 改稱 clean。

正式 Development runner 的程式明確以 `control_engine.DEFAULT_SPEC` 呼叫未修改 v009 Control，Candidate 另以 candidate engine 的 `DEFAULT_SPEC` 執行；沒有使用 Candidate 的 `BASELINE_SPEC` 代替 Control。引擎比較確認兩份 `DEFAULT_SPEC` 唯一欄位差異為 Candidate fold warmup 49、Control 25。候選程式相對 v009 的程式差異是新增 Close 上的 SMA20／SMA50 與訊號 gate，並把 Candidate required history／fold warmup 改為 49；沒有改其他 StrategySpec 門檻。

## 本次新建的準備檔與指紋

所有新報告都在本 worktree，沒有寫入正式 Study 或事件目錄。

| 檔案 | SHA-256／digest | 結果 |
| --- | --- | --- |
| `.study-developer/assignments/TASK-036-v006-resume-20261002.yml` | `01e0c7c7481cab4001d5701d9789dd456300124d7e47d74192b65cce4e24c364` | assignment Schema 通過；含本次原始恢復指令 |
| `research/tsm-divergence-sma20-sma50-regime--v002/create-plan-resume-20261002.yml` | `d1ce1899823ae7e81a0b60f4f66cb2b6352148f9daa8548cf9f4408d57720698` | create-plan Schema 通過；只將 `creator`、`development_actor` 換成本次 assignee |
| `research/tsm-divergence-sma20-sma50-regime--v002/development-plan-resume-20261002.yml` | `9ba61fb95cd62c7caa9803f8ac0b0893e5d1d0fa5bd5c72e3c53c527a4f071c6` | Development-plan Schema 通過；只把外層 `actor` 換成本次 assignee，固定 trial_inputs 與資料不變 |
| `.study-developer/task-036-v006-resume-20261002/native-precreate.json` | `1e83473ccd9da4193e6c9196546b8a4bcf32732837ed1bf59aaedb30f80c41e1` | `passed`，0 errors、0 warnings |
| `.study-developer/task-036-v006-resume-20261002/runner-preflight.yml` | `d62e42ac5b3e8427178cc6c313638b6e7fd441464454d3e4af69afc290618cbe` | `passed`，4 個合成案例 |
| `.study-developer/task-036-v006-resume-20261002/prepare-report.yml` | `256c07fa8dae958825fe8f7b064622337bfbf362db9857bada71572bbbb842d1` | `passed`，`prepare_checks: passed`，含完整 `native_synthetic` |
| `.study-developer/task-036-v006-resume-20261002/prepare-cli-result.json` | `42717c796e6c86281c166232a68b774c23e37907ac8d74fe19ae372c0a6dc772` | CLI 結果為 `completed` |

Prepare 綁定的 source-bundle digest 為 `ea1e654018d4e976f8f964040b6761f6998c466ff0e03e2558a8cc5ff09d7256`，11/11 個列入的來源逐一 bytes digest 通過。其完整路徑與雜湊列在 `runner-preflight.yml` 與 `prepare-report.yml`。本次關鍵研究檔指紋如下：

| 輸入 | SHA-256／digest |
| --- | --- |
| Candidate definition | `38034d16a087215361790c324825ca0b05bd4bcbf746f24e85b6fe4bc23fad0c` |
| Development trial inputs | `1e843da711fd339e943782726df9f093631ab98cd4536acf91919ef25be94ba9` |
| Implementation contract | `01b46a4dc516571677ea08a89a29188fd7818eff561bdefe79c22f26430a81b3` |
| Preregistration | `e12625c614c9737d4c262d5c8292aff75a5ad39833247d72ba842d4d75d94cd5` |
| Qualification spec | `ed28af4c90889dcbfd0f542eb0b6746cc9712e2421b3a4a3636c8cb101a45289` |
| Runner contract | `eb39b8d1e0b2d374a5ab94a795824e550a877d34538c9494b2f18cba173a7391` |
| Candidate engine | `401cc9f72db9b28b2ad5ef4d79abf3f8d00a26b3fc75d0c9dc588ced767c6b8e` |
| v009 Control engine | `f3163c9b92046d0397ce1daf0cfb320a302c9e994875a4be0e93057a83cef7c4` |

## 與先前準備的差異

- PM 交接指出，先前 native prepare／preflight 綁定 worktree `5aa6` 及其 authority。本次報告重新在 `f260` worktree 與上述新 authority 執行，沒有重簽或覆寫舊報告。
- 第一次 v006 派工檔及原始 `create-plan.yml`、`development-plan.yml` 均保留。恢復版三份紀錄是新增檔；create plan 只改兩個 actor 欄位，Development plan 只改一個 actor 欄位，固定 `development-trial-inputs.yml` 的 digest 沒變。
- 本次 Source Bundle 的 11 個檔案全數符合記錄 digest；Candidate engine／v009 engine 與 PM 交接摘要提供的 SHA-256 一致。PM 另已交接其逐 bytes 核對 16 個既有來源未變的結果；我沒有開啟 PM checkpoint 來重做該 16 檔比較。
- Workflow Release／Policy、Source Bundle 與資料的綁定值與交接摘要相同。工作差異是新 worktree／authority、新恢復 assignment 和符合新 assignee 的計畫與報告位置；沒有更換資料或策略門檻。

## 檢查時觀察到的提醒與停止狀態

Runner preflight 和 prepare 各在 stderr 印出兩次 NumPy `RuntimeWarning: invalid value encountered in subtract`（`numpy/lib/_function_base_impl.py:4596`，`diff_b_a`）。兩個 CLI 均完成；保存的 runner／prepare reports 狀態通過，`native_synthetic` 為 `passed`、0 errors、0 warnings。這個 runtime warning 已明確列出供 PM 審閱，沒有被當成正式研究結果。

Runner preflight 的四個分支都使用合成資料（Development 有交易／無交易，以及隔離 runner 的 historical-evaluation 有交易／無交易）；它沒有使用固定 TSM CSV。Prepare 也只執行合成案例。沒有建立正式 Study、沒有寫入 Study event、沒有啟動真實 Development Trial；v002 正式 Study 目錄確認仍不存在。尚未執行 blind review 或成果卡，因為尚無 Development evidence。沒有執行 freeze、Historical Evaluation、Terminal、challenge、replay，也沒有 commit。

本次未開啟 `historical-evaluation-artifacts/`、`.super-admin/` 或 PM checkpoint；只依授權閱讀共享看板 TASK-036。PM 交接中的既有來源曝露限制保留，provenance 維持 unknown。請專案管理者檢查上述完整報告、指紋與 warning 後決定是否放行；收到明確放行前不執行 create 或 Trial。


## PM 初審後追加：候選引擎實際差異（2026-10-02）

兩組完整 unified diff 已另存 `.study-developer/task-036-v006-resume-20261002/candidate-source.diff`，SHA-256=`098bac59e138a7c74d69c6dbceef45d6a651ef7ef6db12bcfdd370a58a3a410d`。檔案分別比較 v002 Candidate 與未修改的 v009 Control，以及 v002 Candidate 與既有 v001 Candidate。引擎來源指紋：v009=`f3163c9b92046d0397ce1daf0cfb320a302c9e994875a4be0e93057a83cef7c4`；v001=`4d0f756827e137b673b2975d654696caeeabd0d46a9e1f44dfa2dae8f5d14888`；v002=`401cc9f72db9b28b2ad5ef4d79abf3f8d00a26b3fc75d0c9dc588ced767c6b8e`。

- **v002 對 v009**：除了描述性文字更新外，Candidate 新增以當日 Close 計算 SMA(20) 與 SMA(50)，並只接受 `SMA(20)` 嚴格高於 `SMA(50)` 的訊號；raw signal 改為原 v009 raw signal 與此條件同時成立。Candidate 的 fold warmup 由 25 改為 49，required-history 推導加入 `50−1`，並更新指標函式與暖機說明。這些程式差異只涵蓋派工授權的單一 SMA regime filter 與 49-session 暖機修正。
- **v002 對 v001**：v001 已有相同的 SMA regime 訊號規則。程式差異只有 Candidate fold warmup 25→49、required-history 推導納入 49，以及說明此暖機長度的註解；沒有第二個訊號變更或其他策略門檻差異。
- 所有已觀察差異都落在已授權範圍；未修改任何 engine、Study 研究輸入、Source Bundle 或既有 prepare/preflight 報告。這次只新增上述 diff 檔並在本 handoff 末尾追加本節；仍未 create 或啟動 Trial。
