---
name: run-strategy-historical-evaluation-v006
description: 由 Study 歷史評估執行者依明確 v006 評估派工，對已凍結的單一 Study 執行唯一 Historical Evaluation 至 terminal；不建立或調整策略。
---

# v006 歷史評估

## 適用角色與範圍

目前對話必須已固定為 **Study 歷史評估執行者**，並收到針對單一 v006 Study 的明確 `historical-evaluation-to-terminal` 派工。candidate（選定候選策略）必須已 frozen（凍結，後續不能更改）。缺少派工、角色不符或尚未凍結就停止回報；不自行換角色、代做 Development，或把「繼續研究」當成評估指令。

先讀根 `AGENTS.md`，再核對以下公開 v006 契約；路徑均相對 repository 根：

- `workflows/strategy-forward-replication-research--v006/reference/operations.md`：派工、評估、恢復入口。
- `workflows/strategy-forward-replication-research--v006/reference/workflow-reference.md`：固定版本解析與執行位置。
- `workflows/strategy-forward-replication-research--v006/reference/multi-asset-input.md`：使用 `data_assets` 時的逐資產規則。
- 同一 Package 的 `schemas/assignment.schema.yml`、`evaluation-plan.schema.yml`、`data-snapshot-set.schema.yml`：實際輸入格式。
- 同一 Package 的 `operations/cli.py`、`operations/evaluation.py`、`writer/service.py`：命令、一次性恢復分支及新增結果的控制。

文件中的 Draft 標題或舊發布測試記錄不代表目前正式狀態；使用有效正式 `release.yml` 與 Study 綁定的 reference 判斷，不使用 `--allow-draft`。

派工紀錄用 canonical YAML（固定鍵排序與格式，便於重算指紋）；可用 `validator.canonical_yaml.canonical_bytes` 保存。必填真實 `source_id`、原文或可追查摘錄 `instruction`、`assigner`、`assignee`、評估角色、Study ID、`workflow_version: v006`、上述 scope 及 `schema_version: 1`。已收到明確指令但尚無紀錄時，可如實建立；不能冒用範例或補造來源。v006 不另要求 Study 核准人、簽名或核准時間，且拒絕核准欄位。派工可早於 candidate freeze，但執行前仍須凍結完成。CLI 不驗證指派者身分或指令真偽；角色字串也不提供作業系統權限。

## 固定輸入後才執行

使用 v006 CLI，先讓工具解析並驗證 Study 的 `manifests/workflow-reference.yml`，再讀 Source Bundle（凍結的程式來源集合）或評估資料。reference 必須指向 repository 內正確 v006 Package，Workflow、release manifest、正式 release record、Policy 集合指紋及 resolver version 均須符合綁定；路徑穿越、符號連結逃離允許位置、版本或指紋不符即停止。不得改 reference、改用新 Release 或以 Study 內複製的 Workflow 代替。

沿用原 authority（保存事件可信順序與啟動控制的記錄位置），固定派工、原計畫、來源、事前研究登記、candidate freeze、snapshot、runner contract。凍結時已通過的原生建立前報告也屬於既有綁定，不重新 prepare、修改報告或另造 passed 欄位。評估 plan 的 `actor` 必須同時符合派工受派者與 Study 的 `historical_evaluation_operator`。任何缺件、資格失敗或漂移都停止回報，不修改策略、暖機、資料區間、資產、runner、門檻或證據來取得通過。

plan 含 `actor`、`data_digest`，且擇一使用：

- 舊式單資產 `data_path`：`data_digest` 是該 CSV 原始 bytes（檔案位元組）的指紋，核對實際檔案，日期清單精確等於 frozen Historical Evaluation snapshot 的 sessions；本版區間為 2020–2024。
- `data_assets`：1–16 筆，按唯一 `asset_id` 排序，恰有一筆 `use: trade`，其餘為 `reference`。每筆固定 provider、symbol、path、自己的 digest、起訖日期、`timezone: America/New_York`、`available_at: after-close`、`interval_role: historical-evaluation`。總 `data_digest` 是去掉 `data_path` 與 `interval_role` 後的逐資產清單 canonical digest，不能拿單一 CSV 指紋代替；清單必須精確等於 frozen snapshot 的 assets，所有日期精確對齊 frozen sessions。CSV 是 `Date,Open,High,Low,Close,Volume` 六欄，使用 XNYS（紐約證券交易所）交易日；每檔最多 32 MiB／10000 列，總量 128 MiB。缺交易日、缺值、非有限數字、無效價格、負成交量或指紋漂移均拒絕，不補值、插值或自動取日期交集。

兩種表示不可混用；`data_digest` 都須等於 candidate freeze 的 `evaluation_snapshot_digest`。輸入路徑由 CLI 在讀取前檢查；多資產路徑不能包含受限資料夾或名為 `evaluation`、`quarantine`、`studies` 的目錄。收盤資料只在收盤後可得，訊號最早決定下一交易日進場；不能把 request 宣告當成程式已證明無前視。

## 唯一操作與恢復

全域參數在子命令前：

```sh
python workflows/strategy-forward-replication-research--v006/operations/cli.py \
  --repository-root <repo> --authority-root <原authority> \
  --role 'Study 歷史評估執行者' \
  historical-evaluation <Study-ID> --plan <評估計畫.yml> --assignment <評估派工.yml>
```

工具在 Study 鎖內建立唯一 reservation（占用本 Study 唯一評估名額的記錄）、started event 與 authority checkpoint，再核對資料，並在 runner 啟動前寫 authority 與本地 launch marker（已進入啟動流程的記錄）。不得並行另啟評估、改計畫取得第二個 operation，或直接呼叫低階 writer、runner 繞過這些控制。已有操作時，用同一 CLI 的 `status <Study-ID>`／`validate <Study-ID>` 唯讀查詢；照樣給全域角色及原 authority，只查指定 Study。

中斷只恢復原 Study、原派工、原 authority 與原 operation：

```sh
python workflows/strategy-forward-replication-research--v006/operations/cli.py \
  --repository-root <repo> --authority-root <原authority> \
  --role 'Study 歷史評估執行者' \
  resume <Study-ID> --assignment <原評估派工.yml>
```

`resume` 讀取已保存的原計畫，不帶新 `--plan` 或自行指定新 operation。依目前 v006 實作判斷：

- reservation 已保存、started event 未完成：由原 operation 恢復事件。
- started 已完成且兩份 launch marker 都不存在：可以接續尚未啟動的 runner。
- 仍在 `historical-evaluation-started` 且任一 marker 已存在：直接走 `evidence-unavailable` 至 `indeterminate`（無法確定），不重新讀取暫存 runner output 或重跑；即使中斷發生在真正啟動前也一樣保守處理。
- 完整 evidence 已發布且 `historical-evaluation-completed` 事件可恢復／已完成：原 operation 接續 terminal，不重跑 runner。

不能刪 marker／reservation、清理部分輸出、改名、換派工或 authority、重建 operation，或手補事件、journal、checkpoint、terminal 與 runtime manifest。遇 `recovery-required`、`evaluation-already-started`、綁定不符或無法安全恢復時，先依 CLI 的 `next_action` 核對原操作；無法恢復就回報，不反覆重試 runner。

## 結果保存與交接

讀寫僅限本次明確派工的 `historical-evaluation-artifacts/<Study-ID>/`，不列舉 store 根目錄或其他 Study。正式結果只能由 v006 writer 新增到這個子目錄；不可覆寫或刪除既有檔案，也不把結果、含結果的日誌或副本保存到其他位置。writer 會核對 evaluator context、唯一 evaluation_operation 及 authority 事件 checkpoint，並以只新增方式寫檔；同名同內容可確認既有檔，衝突內容會拒絕。不得手動補造、搬移或重新命名以避開衝突。

實際工具會在隔離暫存目錄執行凍結的 Workflow、Source Bundle、runner 與 CSV，runner 的 `evidence.yml` 先在暫存執行空間產生，驗證後才由 writer 新增正式 `evidence/historical-evaluation.yml` 與 `evidence/terminal.yml`。這是工具受控的執行過程，不能自行將 raw output 備份到外部目錄。Study operation 永久保存 request、runtime manifest、path／digest 引用及事件控制資訊，不保存 raw output／CSV，也不建立 `runtime/workflow/`；不能把「結果只能在 store 保存」誤解為可以跳過必要流程控制寫入。任何作業系統寫入拒絕都依現有授權與審查處理，不繞過權限或假裝完成。

terminal 後停止。回報 Study ID、operation ID、固定 Workflow reference／Release 指紋、正式 evidence 指紋、terminal outcome 及恢復狀態。`status: completed` 只表示流程已結束，仍須核對 outcome；合法績效 fail 或 indeterminate 都不能稱為通過。未完成時回報 CLI 錯誤碼、實際缺件與 `next_action`，不另跑第二次。
