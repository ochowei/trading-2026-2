# v005 操作契約

本版移除單一 Study 的人工核准。代理可將已收到的明確指令保存為派工紀錄，接續執行指定範圍；不要請使用者另交簽名、核准人或核准時間。只有缺少實際任務範圍、研究決策或 provenance 事實時才補問。

本 Package 尚無有效 `release.yml` 時，不得建立正式 Study。以下 `--allow-draft` 僅能加在隔離測試中；正式使用必須先完成 Workflow Release。所有寫入命令都明示 `--role`，不預設角色。低階 Python `StudyService` 同樣要求 actor、role、assignment；直接發布 artifact、Event 或 recover 也不能繞過。

## 派工紀錄

使用 canonical YAML（鍵排序、固定縮排與型別），可用 `validator.canonical_yaml.canonical_bytes` 寫出。`schemas/assignment.schema.yml` 定義必填內容：指令來源 `source_id`、原文或可追查摘錄 `instruction`、指派者 `assigner`、受派者 `assignee`、角色、Study ID、v005 與範圍。

範圍只有 `development-to-freeze` 或 `historical-evaluation-to-terminal`。前者由 study 開發者執行，後者由 Study 歷史評估執行者執行；本次對話不能自行切換角色。不得把模糊的「繼續研究」或開發交接當成正式評估派工。派工可以早於 source 或 candidate freeze，不要求使用者知道最終指紋後再次確認。

CLI 只驗證結構、角色與 Study 一致性，不驗證指派者身分或原始指令真偽。`examples/assignment.example.yml` 是不可直接當成真實派工的格式範例。

## 開發至凍結

命令入口固定為 `workflows/strategy-forward-replication-research--v005/operations/cli.py`。全域參數必須在子命令前：

```sh
python workflows/strategy-forward-replication-research--v005/operations/cli.py \
  --repository-root <repo> --authority-root <原authority> --role 'study 開發者' \
  develop-to-freeze <Study-ID> --plan <連續計畫.yml> --assignment <派工.yml>
```

連續計畫包含 `create`、`development` 陣列、`freeze` 三部分。依序串接完整 prepare、create、每個 Trial、registry、provenance、readiness、freeze。所有步驟與分段入口共用實作，遇實際缺件或資格失敗會回報，不增加互動式核准。

分段命令：

| 命令 | 輸入與行為 |
| --- | --- |
| `prepare STUDY --report PATH` | 驗證固定研究輸入，隔離執行合成 runner；報告不是派工。 |
| `create --plan PATH --report PATH --assignment PATH` | 依序發布 study-created、preregistration-recorded、development-started。 |
| `development STUDY --plan PATH --assignment PATH` | 執行固定 Trial，驗證 candidate／baseline 並保存 publication 引用。 |
| `freeze-readiness STUDY --plan PATH --assignment PATH` | 在暫存副本走實際凍結規則，不寫入正式 candidate freeze。 |
| `freeze STUDY --plan PATH --assignment PATH` | 依固定選擇次序保存 registry、provenance 與候選凍結。 |
| `terminate STUDY --plan PATH --assignment PATH` | 依合法失敗或證據不足的事實形成 terminal，不改成通過。 |

create 計畫只有 Study ID、creator、identity、完整 preregistration 與 development_actor；creator／development_actor 必須符合受派者。identity 包含 research_round_id、experiment_family、research_owner、historical_evaluation_operator。舊 `create-authorize`、核准事件及核准欄位均拒絕，沒有轉譯入口。

Development 計畫包含 actor、trial_inputs，並擇一使用既有的 `data_path`／`data_digest` 或新的 `data_assets` 清單。多資產清單必須與 Trial inputs 的 `data_bindings.assets` 完全相同；每份 CSV 都只能落在固定 warmup／Development 區間。細節見[多資產資料契約](multi-asset-input.md)。輸出必須符合 `development-envelope.schema.yml`，含 candidate 與 baseline；缺 baseline、未登錄完整 family、provenance 不足、錯誤選擇次序或漂移門檻都不能 freeze。合法績效 fail 仍是有效研究證據。

freeze 計畫包含 actor、provenance 與 snapshot_set。provenance 要保存實際來源和接觸結果的事實，不能自動填 verified-clean。snapshot metadata／session inventory 可用於固定評估資料，不讀取評估價格或結果。候選資格、gates 與 research targets 仍由原 v002 規則重算。

## 一次性歷史評估

```sh
python workflows/strategy-forward-replication-research--v005/operations/cli.py \
  --repository-root <repo> --authority-root <原authority> --role 'Study 歷史評估執行者' \
  historical-evaluation <Study-ID> --plan <評估計畫.yml> --assignment <評估派工.yml>
```

評估計畫包含 actor、data_digest，並擇一使用單一 `data_path` 或多資產 `data_assets`。多資產時 `data_digest` 是凍結於 snapshot 的逐資產清單總 digest，且每份資料自身仍有獨立 digest。不能包含 authorization。actor 必須是 Study 指定的 historical_evaluation_operator；開發派工不能執行評估。工具綁定派工、workflow、Study、authority、source、preregistration、candidate freeze、資料 snapshot、runner contract 與原計畫指紋。

Study 鎖內先建立唯一 reservation，再發布 historical-evaluation-started 及其 checkpoint，之後才能讀資料與啟動 runner。runner 啟動前先保存 authority 與本地 launch marker。完整輸出可重新驗證並發布 completed／terminal；已有 marker 但輸出缺失或不完整時，發布 evidence-unavailable／indeterminate，禁止自動重跑。不同計畫不能取得第二次評估；刪除局部輸出也不能重跑。並行程序只有一個能持鎖，其餘回報待恢復，不同時啟動。

## Workflow reference 與 runtime

Study 建立時先發布不可變的 `manifests/workflow-reference.yml`。其中保存 v005 Package 的 repository-relative 路徑、Workflow digest、release manifest digest 與 Policy set digest；Study 事件與 runner report 都必須帶相同的 reference path／digest。讀取 Study、Source Bundle 或執行 runner 前，先解析並驗證這份 reference；不可用 Study 內複製的 Workflow 取代它，也不可讓路徑穿越 repository 或進入受限資料夾。

Development 與 Historical Evaluation 的 operation 目錄只保存 `runtime/request.yml`、`runtime/runtime-manifest.yml` 及必要的 evidence／artifact 引用。`runtime-manifest.yml` 記錄 Workflow reference、Source Bundle、runner、request、輸入資料與輸出 evidence 的 digest，並明確標示 `execution_workspace: temporary`。實際 Workflow、Source Bundle、runner、資料及 runner output 只放在每次 operation 的隔離暫存目錄；不再寫入 `runtime/workflow/`，也不把同一份 Workflow 複製到每個 Study。

正式 Historical Evaluation 的 raw evidence 與 terminal evidence 只能新增到 `historical-evaluation-artifacts/<Study-ID>/`，不可覆寫或刪除；operation runtime manifest 只保存外部 artifact 的 path／digest。Study 事件保存的是引用與流程控制資訊，不是另一份 Workflow、Source Bundle 或 raw output。

## 恢復與查詢

`status STUDY`、`validate STUDY` 同樣明示全域角色；寫入式 `resume STUDY --assignment PATH` 必須使用原派工。create 的各事件有獨立 journal／checkpoint，不宣稱跨事件原子性。部分成功只能用相同計畫、報告、派工、source 與 authority 恢復；已完成 runner 不重跑。連續計畫也固定保存，resume 會接續原流程。

評估 reservation 已保存但 started 尚未完成時，恢復原事件；started 已完成而 launch marker 尚不存在時，可以接續尚未啟動的 runner。marker 後、真正啟動前的中斷也保守判為證據不足。pause／resume 保留同一 operation，不能退回候選凍結或 Development。

開發角色的 status／validate 僅重建 Development prefix，後續階段標為 not_inspected，不宣稱完整驗證。開發者不能恢復評估；路徑及符號連結在讀取前檢查，錯誤回應不回傳受限 artifact 内容。

JSON 回應包含操作、Study、狀態及可用的 operation_id。錯誤以 assignment-missing、role-mismatch、binding-mismatch、qualification-failed、evaluation-already-started 或 recovery-required 分類，並提供 missing_inputs／scope_boundary；不含 required_approval。角色字串不是作業系統身分認證，仍須遵守 AGENTS.md。
