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
