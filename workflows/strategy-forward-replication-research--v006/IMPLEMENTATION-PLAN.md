# v006 Draft 實作與交接計畫

TASK-037 的實際問題是：通用人造價格能產生均值回歸，卻無法在 SMA20>SMA50 環境形成原生訊號；原暖機推導也只驗到 25 日，沒有核對新增 50 日均線。這份 Draft 修正 Workflow 的案例與契約驗證，不修改公開候選、Policy 或正式 Study。

## 基準與範圍

以 v005 Active 的 102 個發布定義檔案逐一核對並複製，再逐份保存四份 Policy Release。基準 Workflow digest 是 `2441c16d2c477afef9d4d9ca159e3a8bff150080b8552991d5da5fbcc9daf2c2`，Release SHA-256 是 `92c2c35d15e371378c189f60de69093220ab1ee74c256208c36be31534f9aeb8`。不掃描或帶入 v005 studies、runtime、evidence、authority 或根層 release artifacts。Policy 的四份 policy／四份 release 共八個檔案保留相同 bytes，原政策 conformance 程式同樣保留。

2026-09-30 的本次交付是 Draft：尚無根層 manifest、test report、release，未建立真實 Study，未執行任何 Study 或 Workflow Lifecycle，未 commit。正式狀態仍由 Package 外的 `docs/workflow-lifecycle.md` 與有效發布 artifacts 判定。

## 已完成的定義與開發案例

| 交付 | 實際行為與證據入口 |
| --- | --- |
| `operations/synthetic_fixtures.py` | 確定性長期上升＋回檔／反轉與平台；從 Close 獨立重算均線與完整 raw 條件，不注入訊號 |
| `operations/legacy_checks.py` | regime 視窗納入最長就緒；候選／事前登記／契約核對；成立、不成立、相等、未就緒／剛就緒、兩筆 time exit、冷卻第 4／5 步及隔日 open |
| `schemas/implementation-contract.schema.yml` | 新增完整 regime 結構，保留原外部／內嵌指標契約表示 |
| `validator/synthetic_report.py`、`schemas/synthetic-report.schema.yml` | Source Bundle、原來源／同 bytes 副本、引擎、完整契約、spec／cost、Workflow 與報告內容的必要綁定 |
| `operations/service.py`、`operations/preflight.py`、`schemas/runner-report.schema.yml` | prepare 必須附完整原生報告；consumer 與建立前須重算 guard。完整整合執行留給 TASK-038 |
| `operations/synthetic_diagnostics.py`、`tools/`、`examples/` | 可直接跑的人造診斷、原 25 日暖機拒絕示範與 v005 最小根因重現 |
| 完整 `workflow.yml`／rules／schemas／validator／writer／operations／tests／reference | 原有研究、資格、成本、風控、一次評估及資產契約沿用；全部引用明確指向 v006 |
| `reference/sma-regime-root-cause.md` | v005 8／160 個案例失敗、Control、99.25／99.70 與 25／49 就緒缺口的可重現證據 |

## 本次開發檢查

僅執行以下三個開發檔案，不使用會形成 RC 的 `workflow_root` fixture，也不執行 runner preflight、create、development、evaluation 或 terminal 操作：

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  workflows/strategy-forward-replication-research--v006/tests/test_synthetic_regime.py \
  workflows/strategy-forward-replication-research--v006/tests/test_synthetic_binding.py \
  workflows/strategy-forward-replication-research--v006/tests/test_draft_contracts.py -q
.venv/bin/ruff check workflows/strategy-forward-replication-research--v006
```

2026-09-30 的逐輪結果：第一輪 25 passed／1 failed，缺 raw 的錯誤分類由 contract-unsupported 修正為 implementation-invalid；第二輪 48 passed；加入獨立 4／5 步冷卻與 Draft 相容性後 62 passed（7.28 秒），沒有 warnings；再加入實際 demo／CLI 與必要 prepare 原生 Schema／guard 後 66 passed（9.98 秒），沒有 warnings。固定 Draft 斷言已移到隔離副本，最終修正版的命令、退出碼、耗時與靜態檢查結果記於下方驗收紀錄。

必要案例包括：真正的兩種均線值／嚴格相等拒絕、index=48／49 就緒邊界；第 4 步 raw 拒絕、第 5 步接受與次日開盤；同資料 Control；缺／錯 raw、錯均線、冷卻被忽略、提前退出、不可形成核心門檻、契約不支援；來源／報告漂移與必要 Schema；候選／事前登記 regime 不一致、原 fold warmup=25 拒絕；六種內嵌來源、同 bytes manifest 副本／漂移；設定名稱改變不影響人造訊號；1、2、16 資產人造檔案與 0、17 拒絕；v005 102 個定義、Release 與八份 Policy bytes 沒有改變。

所有案例只使用人造價格、公開來源與測試建立的設定。人造 `ready_engine.py` 的 49 日 spec 不代表原候選參數已被允許變更。原 TASK-036 還需 study 開發者依新派工準備一致的暖機／候選契約；本次完整 precreate 保留其 25 日不足的拒絕。

## TASK-038 未執行的完整發布驗收

由被派工的 Workflow 執行者接手：

1. 完整原有測試：canonical YAML、metrics、Policy conformance、assignment／reference、state transitions、immutable evidence、failure／crash recovery、所有 terminal dispositions。
2. 完整 `prepare → runner preflight → 隔離 consumer → create／Trial publication` 整合。特別核對新增 `native_synthetic` 是否在真實產生／驗證報告、consumer 的 Source Bundle 路徑與 workflow reference、create 前重算，以及拒絕缺少或換用候選自行成功報告的行為；這些路徑本次只有定義與開發層級 Schema／函式證據。
3. 單一 CSV 與 1–16 資產的全部 Development／Historical Evaluation 輸入、runner request、snapshot、凍結與一次評估整合，全部使用隔離合成 fixture。
4. 完整 release candidate checker、全套 pytest 與 Ruff；產生新的 manifest／test report 後重跑，確認 Draft／RC／Active 的狀態條件相容。發布檔必須綁定新的 v006 定義，不能沿用 v005 artifacts。

TASK-038 不等於啟用；TASK-039 才依 Lifecycle 由 Trusted Approver 檢視 exact artifacts、核准建立 Release，再由 Workflow 執行者記錄 v006 Active 與 v005 Superseded。既有 v005 Study 原地保留，不自動遷移。

## 最終驗收紀錄

2026-09-30 最終修正版的開發檢查如下。三個限定測試的完整命令已列於上方；此紀錄不具有 Release Candidate 或 Release 效力。

| 檢查 | 退出碼與結果 | warnings／限制 |
| --- | --- | --- |
| 上方三個檔案的限定 pytest | 0；66 passed、0 failed，10.07 秒 | 0 warnings；只驗開發層級函式、Schema、合成檔案與 CLI |
| `.venv/bin/ruff check workflows/strategy-forward-replication-research--v006` | 0；All checks passed | 沒有 Ruff 診斷 |
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python workflows/strategy-forward-replication-research--v006/operations/release_candidate.py` | 0；`definitions-passed`，119 個定義檔 | 不帶 `--candidate`，只讀取與檢查定義，不形成 RC |
| 下方 Python AST 解析 | 0；60 份 Python 定義皆可解析 | 不 import 或執行 Lifecycle |
| `git diff --check -- docs/workflow-lifecycle.md .project-manager/PROJECT_KANBAN.md` | 0；沒有空白格式錯誤 | 只核對這兩份已追蹤的修改 |
| 根因文件所列 `tools/reproduce_v005_fixture.py --repository-root .` | 0；8 次 signal／160 次 holding 搜尋，重現兩個預期 fixture-invalid | stderr 空白；這兩個拒絕是根因證據，不是新增測試失敗 |

AST（只檢查程式能否被 Python 解析）可用以下命令重做：

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
import ast
from pathlib import Path
root = Path("workflows/strategy-forward-replication-research--v006")
paths = sorted(path for name in ("operations", "validator", "writer", "tests", "tools")
               for path in (root / name).rglob("*.py"))
for path in paths:
    ast.parse(path.read_text(), filename=str(path))
print(f"{len(paths)} Python definitions passed")
PY
```

最終根因重現的隔離輸出保存在 `/var/folders/w4/jth3symj3q92qfklnhw_4tx80000gn/T/task037-repro-tfw2dr5e/reproduction.json`；這是可重建的開發暫存證據，不是正式 artifact。候選在 index=49／57／65 的 SMA20=99.25、SMA50=99.70，raw／accepted=0／0；同資料 Control 為 1／1。index=36 的 SMA50 未就緒。

66 個測試內逐一核對了 v005 manifest 的 102 份受保護定義與原 Release SHA-256，以及四份 Policy、四份 Policy Release 的原始 bytes 和 Policy set digest；全部相符。額外對 v005 Package 與兩份公開候選／Control 來源執行範圍限定的 `git status --short`，沒有變更。本次 v006 沒有根層發布 artifacts 或 Study 狀態資料。

TASK-037 的指派交付已完成，共享看板維持 Doing 供 PM 驗收。未執行項目是上節明列的 TASK-038 完整整合／RC、TASK-039 啟用，以及原 TASK-036 需由 study 開發者重新準備的暖機契約；它們都不是本次開發檢查已證明的結果。

## 2026-10-01：完整 Draft 驗收後的重開修正

PM 已驗收 2026-09-30 的 66 項開發檢查；該紀錄保留。TASK-038 執行者接著跑完整 Draft pytest，實際結果是 **83 failed／108 passed／15 warnings，169.51 秒，exit 1**，未形成 RC。完整檢查發現共用舊 fixture 沒有合法契約，不能承受新增原生 guard；開發層級函式通過並不代表整段執行鏈已通過。PM 因此重開 TASK-037，由原 workflow 維護者修正未發布 Draft，完整重跑仍由 workflow 執行者負責。

### 實際失敗與修正

| 問題及影響 | 本輪修正定義 |
| --- | --- |
| 80 項共用 fixture 使用 `{schema_version: 1}` 假契約，且自行填入 prepare passed；consumer 的完整 precreate 正確拒絕 | `test_operations.fixture_repository` 改用完整公開契約、真實 engine／contract runner、資格與 Trial；`passed_report` 取得實際 prepare。`refresh_bundle` 同步重綁事前登記、qualification、engine／procedure 與 Source Bundle，不 mock 或跳過原生檢查 |
| 完整 fixture 修改事前登記後，qualification／Trial 指紋過期 | `repair_helpers.full_repository` 沿用同一完整 fixture，每次改門檻後一致重綁；多資產修改 runner contract 後也重新讀取重綁後的 Trial |
| README 測試只讀第一段，要求 v005 的固定舊句 | 依完整狀態說明檢查 Draft、RC、Active 的有效證據條件，以及只有 Active 可以建立正式 Study；不依賴段落順序或目前 artifacts 不存在的固定聲明 |
| macOS `/var` 與 `/private/var` 指向同一暫存根目錄，但相對路徑比較未一致解析，連續 CLI 變成 recovery-required | `StudyContext` 建立時解析 repository／workflow 根目錄；加入根目錄別名、含 `..` 的別名等價案例，以及根外引擎 symlink 仍拒絕的開發測試；來源／路徑 guard 不降低 |
| 多資產在完整日曆硬插既有 session，可能重複／錯序；故障與 terminal 價格原為 toy runner 設計 | 保留合法完整 XNYS rows，gap 故障明確製造一列重複與缺漏；確認 duplicate-spec 置換真的注入錯誤。terminal pass 以每年人造回檔、次日回檔價開盤與盤中恢復形成真實 target 交易；no-trade 仍為平坦價格，gate-fail 仍由真實交易與原測試門檻拒絕 |
| 原 regime 只有 direct guard／Schema 證據，缺完整 consumer／發布整合 | 新增 `test_regime_pipeline.py`，定義真正 prepare→runner preflight→兩個 Development consumer→create→Trial；保留完整 native_synthetic、來源副本、create 前重算、報告缺失／換用／偽造拒絕、原 25 日整體拒絕 |
| 原完整多資產成功案例只跑 1／2／3，16 僅有輸入 validator 證據 | Development 成功參數保留 1／2／3 並加入 16；多資產 terminal 保留 2／3 並加入 16；17 超額拒絕保留，真正整段結果待執行者驗證 |

新 pipeline 的 baseline 是測試用 `BASELINE_SPEC`：保留同一 SMA20>SMA50 regime、少成交量與收盤反轉兩個訊號條件，執行、成本、暖機同候選。它不是 TASK-036 的公開 v009 Control。原根因與同資料 Control 開發檢查仍使用公開 v009；新 pipeline 定義也直接用相同 rows 核對候選與公開 v009 backtest。測試用 `ready_engine.py` 同時另立 candidate／baseline 的 49 日暖機，原公開候選 `DEFAULT_SPEC=25` 沒有修改。

本輪修改的 Package 定義：

- `operations/legacy_checks.py`。
- `tests/test_release_candidate.py`、`test_operations.py`、`repair_helpers.py`、`test_multi_asset.py`、`test_assignment_lifecycle.py`。
- `tests/test_synthetic_binding.py`、`test_draft_contracts.py`、`fixtures/regime/ready_engine.py`。
- 新增 `tests/fixture_prices.py`、`regime_pipeline_helpers.py`、`test_regime_pipeline.py`。

### 開發結果、定義凍結與交接

仍只使用前述三個限定開發 pytest 檔案；沒有執行新的 `test_regime_pipeline.py`、完整 pytest、runner preflight、prepare、create、連續入口、Study Lifecycle 或任何 RC 產生步驟。

新限定檢查第一輪是 **74 passed／1 failed，15.51 秒，exit 1，沒有 warnings**。新增 terminal 正例的真實引擎雖形成 35 筆交易，原通用價格在恢復後以 100 開盤進場、平台退出，只產生成本損失；固定 floors 正確拒絕。修正人造價格為訊號次日仍以回檔價開盤、盤中恢復並由 target 成交，沒有更改引擎或政策。修正版的同一限定命令為 **75 passed／0 failed，15.61 秒，exit 0，0 warnings**。增加的九項只驗共用 fixture 唯讀 precreate、別名／逃逸拒絕及人造價格在記憶體內的真實交易／固定 floors 重算，沒有建立 Study 或正式結果。

最終 `.venv/bin/ruff check workflows/strategy-forward-replication-research--v006` 為 exit 0、All checks passed；唯讀 `operations/release_candidate.py`（不帶 `--candidate`）為 exit 0、122 個 definition files；前述 AST 命令為 exit 0、63 份 Python 定義可解析。v005 102 份受保護定義、原 Release SHA-256、八份 Policy／Policy Release bytes 均相符，公開候選與 Control 的範圍限定 git status 無變更。

本輪凍結的 **Draft Workflow digest** 是 `bcbc215e2ccf0c50317212d3d6c7d792442d826e39770787e3a4668082ea76a9`。本段計畫與看板紀錄不在發布定義 digest 內；凍結後不再修改會進 manifest 的定義，直到 TASK-038 回報需要由維護者修正的具體問題。

TASK-038 應對這份確切定義重新跑完整 pytest／Ruff／checker，包含新增 SMA pipeline、原故障／恢復／state／terminal 語意、單一 CSV、1／2／3／16 完整多資產路徑及 17 拒絕。完整通過後才能形成 RC，再在 RC artifacts 存在時重跑；75 項 direct-function 開發結果不能代替整合證據。原 15 warnings 保留，由執行者記錄新輪 warnings；本輪沒有以忽略 warnings 或降低 Schema／Workflow／Policy 取得通過。TASK-037 維持 Doing 等待 PM 驗收與同一執行者接續。

### 原失敗證據入口

PM 明確准許本輪維護者讀取的純合成外部日誌位於 `/private/tmp/task038-v006-release-20261001-1ib8gl60/`，讀取前已核對：

- `draft-pytest.log`：SHA-256 `509f593bb5ad19f45940261343f75b689b66d61873ebc249c96c52bfaedfdf40`。
- `draft-representative-failures.log`：SHA-256 `003bd56c426b988611c1f5cc5fd65bd6926842f3318e2149e8f726c102076cbd`。
- `draft-continuous-diagnostic.log`：SHA-256 `80be975cda29d553ebba4d893b5f025dba8c3e4d283a2162ed187ec0066d6f68`。
- `draft-failure-inventory.json`：逐案分類為 80 個完整原生拒絕，加各一個事前登記指紋、README 舊句與路徑別名失敗。

這些都是執行者在專案外隔離副本產生的人造測試日誌。本維護者沒有執行該診斷 script，也沒有讀取真實 Study、正式結果庫或其他角色專屬資料。

## 2026-10-01：r2b 整合觀察斷言修正

TASK-038 的 r2b 完整 Draft pytest 結果為 **206 passed／1 failed／0 errors／0 skipped／211 NumPy warnings，635.30 秒，exit 1**。唯一失敗是新 SMA pipeline 測試把已完成的原生觀察次數誤寫成 4，實際為 8；原生檢查並沒有失敗。先前所有成功、失敗與中止紀錄均保留，本節不替代原 66 項驗收、83／108／15 首輪完整結果或上一輪限定開發紀錄。

只修改 `tests/test_regime_pipeline.py`，斷言與公開程式的實際路徑一致：

1. 每個 Development consumer 建原生報告一次，再由 `operations.create`、`writer.create_study`、`writer.append_event(study-created)` 各重驗一次。因此依 Development case 數推導 consumer 數，總數精確為 `consumer_count * 4`；同時逐一核對每個 consumer 正好有四份報告、每份內容與 prepare 回傳的原生報告相同。不是改成寬鬆的 `>=`，也沒有減少任何 guard。
2. 外層 create 沿同樣三個既有驗報入口重算，精確核對三次都是目前 repository。每次原生重算與報告觀察都要求尚無 `events/*.yml` 事件檔；允許 writer 先建空目錄，避免把空目錄誤當第一事件已發布。
3. 候選／同資料公開 v009 backtest、短暖機與錯誤報告拒絕、consumer 報告一致、Trial、同 bytes 凍結副本及副本漂移拒絕都保留。

本輪沒有修改 Policy、引擎、門檻、數值公式或 warnings 設定來消除 211 warnings。它們屬於執行者 r2b 的真實 NumPy 診斷，後續單案／完整 Draft／RC 重驗仍須如實記錄。

維護者再次只執行原三個限定開發檔案：**75 passed／0 failed，15.54 秒，exit 0，0 warnings**。Ruff 為 exit 0、All checks passed；唯讀定義 checker 為 exit 0、122 個 definition files；AST 解析為 exit 0、63 份 Python 定義。新的凍結 **Draft Workflow digest** 為 `e527578ca62d907d5b1e16f57d5a4c52f0b7cabb9d616970eb2eb2e383f8e7a9`，取代上一輪待驗凍結 digest，尚未形成 RC。

PM 明確准許唯讀的外部純合成材料：`/private/tmp/task038-v006-release-20261001-1ib8gl60/r2b-draft-pytest.log`（已核對 SHA-256 `e023704c12b5664c20ef9b4294e5048ff92c2660f166a344d7acb75ac4b5e430`）、`r2b-draft-pytest-junit.xml`、`r2b-failure-inventory.json`。本次核對 log 指紋與 inventory／trace，沒有執行其中 pipeline 或讀取真實結果。

維護者沒有跑新的整合案例、完整 suite、Lifecycle 或 RC。TASK-037 維持 Doing；同一 TASK-038 執行者先跑單一 `test_regime_prepare_consumer_create_trial_and_frozen_source_copy` 診斷，接著完整 Draft 與 RC 重驗。定義已凍結，後續只追加 excluded 計畫／本任務交接，若再有具體定義缺陷由 PM 交回維護者。

## TASK-038 實際發布檢查：第一輪未通過（2026-10-01）

workflow 執行者依明確派工執行完整 Draft 發布驗證。191案實際結果為108 passed、83 failed、15 warnings，exit 1，169.51秒；完整命令、trace、warnings、elapsed及SHA-256保存在專案外 `/private/tmp/task038-v006-release-20261001-1ib8gl60/draft-round-1-handoff.md` 與各 `.log`／`.json`。完整pytest日誌SHA-256為 `509f593bb5ad19f45940261343f75b689b66d61873ebc249c96c52bfaedfdf40`。所有操作僅使用人造fixture與專案外隔離暫存目錄。

80案的shared fixture不符合新增完整原生precreate；另有完整prepare的qualification／trial prereg digest過期、README固定句測試不符合目前段落，以及consumer的 `/var`／`/private/var` 別名造成relative_to ValueError。新regime尚缺完整prepare／runner-preflight／consumer／create／Trial整合成功，以及報告替換、缺失與來源副本等反例。上述修正需求已交PM，由workflow維護者處理；執行者沒有修改定義、程式或測試，也沒有降低門檻或移除guard。15個NumPy warnings原樣保留。

Ruff與119定義的canonical YAML／Schema／Policy definitions checker均exit 0；測試前後核對v006 Draft digest仍為 `be58a60f4165140fdf27c2a0d34ea1546f58c28897c6cdda6484edb504b3e34a`，v005的102受保護定義、原Release與八份Policy/Release bytes仍相符。完整驗證失敗，停止依賴性RC形成；未建立根層manifest、test report、release或真實Study，TASK-038維持Doing待修正與重跑。v005仍Active。

## TASK-038 修正版完整發布檢查：第二輪未通過（2026-10-01）

PM確認修正版122份定義的指紋為 `bcbc215e2ccf0c50317212d3d6c7d792442d826e39770787e3a4668082ea76a9`，執行者先重核相同內容及v005／Policy基準。序列pytest在60個通過進度標記後，依PM指示安全中止並改用環境現有pytest-xdist四程序完整重跑。序列run的pytest exit=-15、沒有完整JUnit，並未列成整套通過；全部中止及停程序證據保留。

完整四程序Draft共207案，實際為206 passed、1 failed、0 errors、0 skipped、211 warnings，exit 1，635.30秒。唯一失敗在新增SMA正向完整管線的觀察次數：兩個consumer實際各經報告建立與三層create前guard，共8次，測試硬寫4次。後面的外層create也應觀察三層重算，而非只要求1次；本輪尚未到達該後段。實際guard全部保留，由維護者修正觀察斷言，執行者未修改定義。

完整log及SHA-256：`/private/tmp/task038-v006-release-20261001-1ib8gl60/r2b-draft-pytest.log`、`e023704c12b5664c20ef9b4294e5048ff92c2660f166a344d7acb75ac4b5e430`。同目錄的 `draft-round-2b-handoff.md` 保存完整命令、JUnit、trace分類、逐檔實際覆蓋及211個NumPy warnings。16資產Development／request／snapshot／freeze／一次評估到terminal、26個crash recovery及舊狀態案例均通過，但新增SMA正向create／副本／Trial尚不能宣稱完成。此管線baseline是候選自身的合法BASELINE_SPEC；同資料v009 Control是直接引擎比較，不代表TASK-036原訂baseline管線或暖機準備。

Ruff、122份definitions checker與測試後保護基準均exit 0，v005的102定義、3份發布檔及8份Policy／Release仍相符。第二輪仍停止依賴性RC形成，沒有根層manifest、test report、release或真實Study，TASK-038維持Doing等待修正與完整重跑；v005仍Active。舊失敗與中止日誌原地保留。

## TASK-038 最終 Release Candidate 交付（2026-10-01）

PM與維護者交接的122份固定定義為 `e527578ca62d907d5b1e16f57d5a4c52f0b7cabb9d616970eb2eb2e383f8e7a9`。執行者先對新增SMA完整pipeline單案實際診斷：1 passed、0 failed、3 warnings，17.56秒、exit 0；先前斷言後半的create／來源副本／Trial與副本漂移拒絕已實際完成。接著完整Draft四程序pytest為207 passed、0 failed、0 errors、0 skipped、212 warnings，629.83秒、exit 0。Ruff、canonical YAML／schemas／Policy definitions checker、測試前後固定定義與受保護基準全部exit 0。全部Lifecycle只用專案外人造fixture，測試前已重核tmp_path與真實Package唯讀邊界。

完整Draft通過後，以既有canonical YAML及build_release_manifest形成兩份RC檔。manifest／初版report存在時完整重跑pytest，207 passed、0 failed、0 errors、0 skipped、212 warnings，822.51秒、exit 0；RC Ruff及 `release_candidate.py --candidate` exit 0。PM另在不同外部目錄對相同初版bytes獨立完整執行207 passed、0 failures／errors／skips、212 warnings，801.75秒、exit 0。等待PM明確告知全套結束後才定稿report，PM結果另列一項check，沒有混為執行者結果。最終report有10項實際成功檢查；report schema、完整manifest、candidate checker及v005／Policy保護基準再次全部exit 0。先前83失敗、1失敗、序列exit=-15與所有warnings仍保留，沒有把失敗或中止列成全套通過。

最終三個SHA-256：Workflow定義集合 `e527578ca62d907d5b1e16f57d5a4c52f0b7cabb9d616970eb2eb2e383f8e7a9`；`release-manifest.yml` 為 `e87dbb536b95c7b7e3ec9842732cb6d87a6db3fb9238262841cde16ba4880882`；`release-test-report.yml` 為 `e7028200de3a9ed38b321d666c741234ac7306edf34f66b00dbccc8b211bf8fe`。manifest bytes在兩套RC全套及報告定稿前後皆未變；122份發布定義沒有改動。

完整外部交接與覆蓋對照：`/private/tmp/task038-v006-release-20261001-1ib8gl60/r3-final-handoff.md`；逐項實際命令／exit／elapsed／warnings／log SHA索引為同目錄的 `r3-final-command-ledger.json`，最後保護證據為 `r3-final-digests-and-protection.json`。Draft log SHA=`07731c00f357c4d38992d5cf2db49ac0472c800f62d3154aa5dd6d8d93824d1a`；RC log SHA=`5e93d2aed74c537d0aa1e3079ce9b281bb4a664882c24c0fbff503b96286c817`；final-verify log SHA=`642d4beb67b3c554b619fdd8230f0c373b2aef7fcb4833ca2bcb53f70e72ee5b`。所有日誌與fixture留在專案外，沒有放入Package digest。

新增SMA真正prepare／runner-preflight／兩consumer／create／Trial、八份consumer原生報告、首次事件前的三層重算、來源副本、報告缺失／替換／重新簽名造假拒絕、25日不足暖機均有成功與反例證據。單CSV、1／2／3／16資產Development及2／3／16資產freeze／唯一評估至terminal、26個crash recovery、47個assignment／state、固定Policy與floors全部通過。沒有宣稱4–15資產逐一各跑E2E；SMA管線baseline仍是候選自身BASELINE_SPEC，公開v009 Control是同資料直接引擎比較，不是TASK-036原訂baseline pipeline或真實Study／暖機重新準備。

v005的102份manifest明列定義、3份root發布檔與8份Policy／Release原始bytes均與最初保護基準相符，v005原Release SHA仍為 `92c2c35d15e371378c189f60de69093220ab1ee74c256208c36be31534f9aeb8`，Policy集合仍為 `c86066b33119366a3172f475ff75f8813ba4b7545571894edfe581afabe32215`。TASK-038維持Doing供PM最終驗收；v006保持Release Candidate、v005仍Active。未建立根層release.yml、真實Study、真實stores或批准；未啟用、處理其他任務或commit。執行者沒有修改definition／code／tests。
