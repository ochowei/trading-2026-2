# TASK-036 v006 建立前 checkpoint

Study：`tsm-divergence-sma20-sma50-regime--v002`。固定角色為 study 開發者，TASK-036 已接手 Doing。完整檢查完成，等待 PM 審閱及接續通知；未建立真實 Study 或啟動真實 Trial。

## 已固定的研究與比較

Candidate `tsm-mr-v009-sma20-over-sma50-regime-v002` 只有訊號日 Close 含當日 SMA20>SMA50 濾網；Control `tsm-mr-v009-two-stage-volume-reversal-control-task036-v002` 使用未修改 v009 的完整 DEFAULT_SPEC，不用候選的 BASELINE_SPEC。13 個 Development gates、研究目標空集合、唯一 Candidate／Trial、短期超跌、volume、RSI、10 session持有、5 session冷卻、±4%退出、risk2%、base/stress成本都維持舊準備設定。

Control 正式路徑為研究 runner main 的 development 分支 → `model_evidence(module=control_engine, spec=control_engine.DEFAULT_SPEC)` → 原 v009 `backtest` 分別以 BASE_COST／STRESS_COST 執行。Candidate 為同一 runner 的另一臂，以新 regime_v002.DEFAULT_SPEC 執行。兩臂共用同一 request CSV、signal_start=2014-01-01、signal_end=2018-12-31，base/stress費用分別每側1／2bps，滑價每側5／20bps。

Control required history 與 fold warmup 仍為25先前sessions；Candidate 的SMA50含當日，required history及fold warmup同步49。正式 Development request 含完整2013全年暖機，兩臂最長指標於2014起始前均已就緒；Development都以同一2014–2018期間決定訊號且完整退出，未額外縮短任一臂交易期間。這個技術就緒差異已在 candidate、preregistration、implementation contract及trial inputs固定。未以診斷v009對照冒充正式baseline結果，尚無真實Development結果。

來源差異精確見 `/private/tmp/task-036-v006-checkpoint/candidate-source.diff`：fold暖機25→49、required-history max納入49、說明文字25→49。AST核對（去除說明文字後比較程式結構）確認指標、所有成交／風控／持有／退出函式不變；backtest可執行程式完全相同。v001／v009及舊research／private準備16個原檔完整bytes指紋均未變。原文指紋紀錄於 preserved-originals.yml，本次輸出 checkpoint 不授予直接讀取私有原檔的權限。

## 完整檢查

- Release validator重算通過，v006 Active；Workflow `e527578ca62d907d5b1e16f57d5a4c52f0b7cabb9d616970eb2eb2e383f8e7a9`、manifest `e87dbb536b95c7b7e3ec9842732cb6d87a6db3fb9238262841cde16ba4880882`、report `e7028200de3a9ed38b321d666c741234ac7306edf34f66b00dbccc8b211bf8fe`、release檔 `61d6eeebe58fdd40d6805ca461ccc9a327b9aa153eedd6414a612ddc5ad3594f`；policy set `c86066b33119366a3172f475ff75f8813ba4b7545571894edfe581afabe32215`。
- Native precreate `passed`、error_count=0、warning_count=0；完整JSON為 precreate-report.json。契約、identity、Source Bundle、參數、gates、全部就緒及合成guard實際完成。
- runner-preflight `passed`，完整 runner-preflight-report.yml。Development有交易案例Candidate／Control各1筆；無交易案例Candidate0、Control1。另兩個2020日期案例完全由runner contract人造OHLCV產生，只查介面，未讀任何正式價格或真實評估evidence。
- prepare `passed` 且 prepare_checks=passed；完整 prepare-report.yml SHA256 `41b54e0ad58c5c6540926b047ebedd0fc14746461b21ddaaa43863bf2951b930`，含完整 native_synthetic：契約／原契約来源／Source Bundle／引擎／spec／cost／Workflow／報告指紋。原生passed cases=['rsi', 'readiness', 'regime', 'cooldown-boundaries', 'intraday-exit', 'holding-cooldown']；first_ready_index=49；above/below/equal/not-ready/just-ready、raw/accepted、持有／冷卻、stop/target/gap等均依真實價格計算。prepare同runner隔離consumer有實際create／publication驗證，僅在TemporaryDirectory，正式Study與authority仍不存在。
- Source Bundle 11/11 bytes吻合。canonical與create／Development／assignment schema檢查通過；本次目標路徑 git diff --check 通過。未新增一般測試或執行pytest。
- runner-preflight及prepare各輸出2次NumPy `invalid value encountered in subtract` warning，来自極小人造案例的無限PF統計；保留實際warning紀錄，不當作native warning_count或正式績效結果。完整驗證仍通過。
- 唯一實際CSV hash `a42c3932a4cb825e0025f564b3dca34bd755c9173789951232e678b7250f46f7`；2013-01-02–2018-12-31、1510列、完整XNYS日期驗證，data-check.yml。未讀2019或2020–2024真實價格。

## 可追查輸入與身份

Research根目錄：`/Users/william/.codex/worktrees/5aa6/trading-2026-2/research/tsm-divergence-sma20-sma50-regime--v002`。Candidate source：`/Users/william/.codex/worktrees/5aa6/trading-2026-2/src/trading_2026_2/tsm_mean_reversion_two_stage_volume_reversal_sma20_sma50_regime_v002.py`。
派工公開副本：`/Users/william/.codex/worktrees/5aa6/trading-2026-2/research/tsm-divergence-sma20-sma50-regime--v002/assignment.yml`；source_id=`codex-project-manager-task:TASK-036:v006:2026-10-02`，含使用者原文及共享看板PM派工定位；assigner=專案管理者 /root、assignee=/root/task_036_v006_development。Schema scope development-to-freeze唯一開發值不擴張本次授權；instruction明限Development、checkpoint前不得create、禁止freeze／terminate／正式評估／Terminal／challenge／replay／commit。
create-plan.yml固定research_round_id=`tsm-divergence-sma20-sma50-regime--v001`、experiment_family=`tsm-mean-reversion-v009-sma20-sma50-regime`，保留既有研究身分脈絡；owner=`ochowei@gmail.com`、operator=`operator A`。Development-plan.yml綁定唯一Trial及實際Development資料。原authority=`/Users/william/.codex/worktrees/5aa6/trading-2026-2/.authority`；reference digest=`cfe747174027f22b45f6c699cd1675753abedca2a71ed6035cf7626064e906f1`。

| 新輸入 | SHA-256 |
|---|---|
| `assignment.yml` | `3c09c56860c7bfc676e317870861d76c35a3e04d68c4a062ce9c0b7151ed6301` |
| `candidate-definition.yml` | `38034d16a087215361790c324825ca0b05bd4bcbf746f24e85b6fe4bc23fad0c` |
| `create-plan.yml` | `5a33c27d07a8c3aa8045dbd73af8709d31489f873f4a9c237759741254afa8af` |
| `development-plan.yml` | `dd8fd4ab22d18d9e9ed8f6d7184092d043f22f14cd12247d6eba724b2f7eb8cb` |
| `development-trial-inputs.yml` | `1e843da711fd339e943782726df9f093631ab98cd4536acf91919ef25be94ba9` |
| `implementation-contract.yml` | `01b46a4dc516571677ea08a89a29188fd7818eff561bdefe79c22f26430a81b3` |
| `preregistration.yml` | `e12625c614c9737d4c262d5c8292aff75a5ad39833247d72ba842d4d75d94cd5` |
| `qualification-spec.yml` | `ed28af4c90889dcbfd0f542eb0b6746cc9712e2421b3a4a3636c8cb101a45289` |
| `run_development.py` | `02a5d14fe751ad14d431560e172af4304577fe44ba91ff37f80be5cbd9653d5a` |
| `runner-contract.yml` | `eb39b8d1e0b2d374a5ab94a795824e550a877d34538c9494b2f18cba173a7391` |
| `source-bundle.yml` | `ea1e654018d4e976f8f964040b6761f6998c466ff0e03e2558a8cc5ff09d7256` |
| `synthetic_preflight.py` | `896aa7103e3177e5e28bfd94c73f0407ffd3b8da6692bf8365baa36e8b2da523` |

其餘精確路徑及完整指紋見 fingerprints.yml；release-check.yml、data-check.yml、checkpoint-facts.yml、candidate-source.diff、precreate-report.json、runner-preflight-report.yml、prepare-report.yml都在此外部目錄，可供PM審閱。

## Provenance與邊界

目前provenance-unknown：先前已知v004 preregistration的v009績效數字來源／期間／階段未明；新StudyID不抹除過往來源或曝光。本輪未查看正式Historical Evaluation或Terminal結果，但開發者已接觸派工／prepare流程資訊，不能宣稱state全盲。prepare隔離consumer的synthetic-fixture身份不能冒充真實clean來源。後續PM另行安排獨立Development-only盲檢討。

精確檢查v005/v006下v001/v002正式Study目錄及新v002authority不存在。未建立真實Study、event或operation；未啟動真實Trial；未freeze/terminate/HE/Terminal/challenge/replay或commit；未讀受限資料夾或正式結果。checkpoint完成維持Doing，等待PM接續通知後才能create與唯一Development。
