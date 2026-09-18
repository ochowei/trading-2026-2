# v002 日常操作、恢復與 Skill 交接

本版交付終點是 Release Candidate。只有核准者建立有效 `release.yml` 後才能用於正式 Study；不可對正式研究使用 `--allow-draft`。下列命令中的 `python` 應指向研究環境的同一個 Python，`<repo>` 為 repository 絕對位置。新 Study 預設 authority 是 `<repo>/.authority/`；既有 Study 必須使用原位置，可在子命令之前明示 `--authority-root <bound-root>`。

## 正常流程

```text
prepare → create-authorize → development（每個預先登記 Trial 一次）→ freeze
```

| 操作 | 使用者提供 | CLI 完成 |
| --- | --- | --- |
| prepare | 研究 bundle 與人工合成案例 | ID、authority、規格、策略合約、策略邊界及完整 runner／Trial 消費驗證 |
| create-authorize | 與該研究綁定的既有核准 | 保存原計畫，依序建立三個獨立事件 |
| development | 已凍結 Trial inputs、該階段資料及操作者 | 真正 runner、candidate／baseline 保存、發布清單、Trial 登錄 |
| freeze | 真實 provenance、snapshot metadata、操作者 | 先完整模擬，通過後發布 registry、provenance、candidate freeze |

每一步仍執行必要驗證；不必再手動串 `studyctl all`、authority checker 或低階 writer。診斷時可使用 `runner-preflight`、`freeze-readiness`、`status`、`validate`。v001 共用工具與技能的原介面不變。

## 準備研究 bundle

在新 `research/<id>/` 以不可覆寫方式建立 preregistration、qualification-spec、candidate-definition、implementation-contract、development-trial-inputs、source-bundle 及 runner-contract。Source Bundle 列出兩個正式 runner、策略引擎、必要 package `__init__.py`、研究程式依賴及 frozen 設定；不要依賴另一個 checkout 的 editable install。CSV 不列為可複製 source；資料另以 digest 綁定。

多 Trial 必須事先列入 `complete_candidate_family`，其他 Trial 的 inputs 放在 `trial-inputs/*.yml`，各自 digest 由 prepare settings 綁定（或已存在 Source Bundle）；避免把含 source_bundle_digest 的 inputs 放入該 bundle 造成指紋自我參照。研究期間不能另造 inputs 冒充原 Trial。Development 輸入檔須只含允許的暖機及 Development 日期，不要把含 Evaluation 年份的整檔交給 runner 再期望它自行避開。

```bash
python workflows/strategy-forward-replication-research--v002/operations/cli.py \
  --repository-root <repo> prepare <id> --report <prepare.yml>
```

失敗不留下正式 Event 或 checkpoint。報告綁定 source、主要設定、工具內容、Python 執行檔／版本、套件版本與合成資料指紋；建立前任何變更均須重新 prepare。報告檔不能覆寫，重做請用新檔名。

## Runner 契約與證據消費

兩種 runner 都接受 `--request <canonical YAML> --output <canonical YAML>`。canonical YAML 是固定序列化格式，使相同內容具有相同指紋；小數用字串，不使用 YAML float。

正式與合成執行均呼叫 `operations.preflight.launch`：同一 Python、`-m operations.launch`、隔離 repository 工作目錄，以及 package／repository／src 模組路徑。request 包含 `stage`、`data_path`、`data_digest`、`preregistration`、`trial_inputs`、`source_bundle`。runner 不得依合成模式另走一套策略或輸出實作。

Development 輸出包具有 `candidate` 與 `baseline`；各自包含 base／stress raw trades、metrics、diagnostics、gates 與內容綁定。共用 consumer 驗證兩者並分別保存，產生 publication manifest（列出精確檔案位置、指紋及輸入的發布清單），Trial 指向其中 candidate；baseline 不參加候選排名，但不能省略或丟棄。獨立 validator 會重讀兩份證據並重算。

Historical 輸出使用 `historical-evaluation.schema.yml`。preflight 的每種 runner 都須涵蓋有交易與無交易，並可加主要分支的 `required_output_keys`。Development preflight 還在 TemporaryDirectory 中真正建立合成 fixture、發布 candidate／baseline、追加 Trial 並驗證 checkpoint；所有這些資料隨暫存目錄移除，不是正式研究或授權。

```yaml
protocol: request-output-v1
synthetic_only: true
runners:
  development: research/example/run_development.py
  historical-evaluation: research/example/run_evaluation.py
cases:
  # 每階段各至少一個 trades 與 no-trades。
  # 每個 case 有 stage、expect、rows。
  # rows 每列是日期、Open、High、Low、Close、Volume，必須為人工合成值。
```

此段只是格式示意；可執行的案例由 `tests/repair_helpers.py` 產生，完整驗收是 `tests/test_repairs.py::test_cli_prepare_to_freeze_same_engine_without_guard_bypass`。

Python 啟動器拒絕網路、外部程序、隔離範圍外讀取、輸出目錄外寫入；允許 Python 環境及時區唯讀。這延續可信操作者模型，並非防惡意原生擴充的 OS 沙箱；正式環境仍須離線、沒有券商下單權限。

## 建立與核准

`create.yml` 包含 study_id、creator、identity（research_round_id、experiment_family、research_owner、historical_evaluation_operator）、完整 preregistration、preregistration_actor／preregistration_approval、development_actor／development_authorization。

兩份既有核准均包含 decision=approved、actor_id、role（trusted-approver 或超級管理者）、approved_at、非空 basis；scope 分別為 preregistration、development-only。bindings 必須完整包含 study_id、workflow_version=v002、source_bundle_digest、preregistration_digest。這是可追查的核准陳述，不是工具替人簽核，也不是密碼學身分認證。

```bash
python workflows/strategy-forward-replication-research--v002/operations/cli.py \
  --repository-root <repo> create-authorize --plan <create.yml> --report <prepare.yml>
```

工具保存原計畫與報告，依序發布 study-created → preregistration-approved → development-authorized。各 Event 有獨立 journal／checkpoint，**沒有跨事件原子性**。validate／append／recover 都會重驗原報告與核准引用；刪除或換成另一 Study 的文件會失敗。歷史驗證比對當時保存的 bytes，不要求今天的 Python 套件版本與當時相同。

## Development 與候選資格

`trial.yml` 包含 actor、完整 frozen trial_inputs、repository 相對 data_path 及 data_digest；資料須與 inputs.data_bindings.development_digest 一致（若已登記），且日期不能進入 Evaluation。

```bash
python workflows/strategy-forward-replication-research--v002/operations/cli.py \
  --repository-root <repo> development <id> --plan <trial.yml>
```

同一 operation 已有輸出時，只完成驗證與發布，不重跑 runner；已有 started 記錄但無完整輸出時停止自動恢復，需判定 exposure 與可恢復性。不能從「沒有 evidence」推斷沒有看過資料或結果。

exit code 0 表示操作完成，不等於研究合格。回應的 assessment 分開顯示正式 gates、research targets、evidence validity、candidate freeze eligibility。無交易與 gate fail 可以是有效且執行完成的結果；不得因為績效不佳反覆重跑同一 Trial。Research target-only fail 不加入 formal failed_gates；未登記 targets 顯示 not_registered。

目前可排序／計算 target 的數值限 validator 已從 raw trades 重算的 metrics，清單在 `validator/qualification.py`。支援數值 ascending／descending 加 stable-trial-id 同分排序，或 fixed-single-candidate-no-outcome-ranking；未知 metric／規則在 prepare 拒絕。零交易統計用 `empty_development_result` 明示不可估計，不捏造 bootstrap。

## 凍結

`freeze.yml` 包含 actor、provenance（真實 status、sources 及 exposure 事實）及 snapshot_set（既定 schema 的完整 session metadata，不是 Evaluation 價格或結果）。CLI 從 raw evidence 重算完整合格集合及排名，從 prepare 取 candidate／qualification 指紋，產生 selection；使用者不用手填這些結果。

```bash
python workflows/strategy-forward-replication-research--v002/operations/cli.py \
  --repository-root <repo> freeze <id> --plan <freeze.yml>
```

freeze-readiness 使用同一 plan，在隔離副本模擬所有未完成事件，不先寫一半正式 registry。freeze 本身已包含 readiness；只有診斷時才額外呼叫 `freeze-readiness <id> --plan <freeze.yml>`。registry 完整性、provenance 與候選資格分開判定；低階 writer 也不能用自行宣稱的 eligible 名單繞過。

## 恢復與提前終止

```bash
python workflows/strategy-forward-replication-research--v002/operations/cli.py --repository-root <repo> status <id>
python workflows/strategy-forward-replication-research--v002/operations/cli.py --repository-root <repo> resume <id>
```

operation 保存原 plan 與完成狀態；相同步驟不接受不同 plan。恢復先在隔離副本驗證原 prepared journal、references 與 checkpoint，再補發相同 bytes；不重新產生已準備事件的時間。macOS／Linux 使用 flock，程序死亡會釋放持鎖狀態，鎖檔保留且不 unlink。不要人工刪鎖、換 frozen inputs 或重建 Study。不支援 flock 的平台不降級成不安全鎖。

`terminate <id> --plan <terminal.yml>` 是明確的終止操作，不是所有錯誤的自動重試。不可恢復缺證據的 plan 包含 actor、evidence_unavailable（stage、unavailable_path、reason）、terminal_evidence（schema_version、outcome=indeterminate、authority=none、recomputed=true、reasons）；bindings 由 CLI 根據事件鏈組裝。完整 family 均不合格時，使用 reason_kind=no-eligible-candidate 與 outcome=fail，由 CLI 先發布 candidate_available=false 的 registry，再終止。

## Evaluation 交接

開發 skill 到 candidate-frozen 停止。開發者的 status／validate 只做 Development prefix 的語意驗證；遇到後續評估／terminal 會明示 not_inspected，不開啟正式結果 store，也不把事件存在與否當成 blind review exposure 事實。

只有既定 Evaluation 角色及使用者明確要求才能執行：

```bash
python workflows/strategy-forward-replication-research--v002/operations/cli.py \
  --repository-root <repo> --role 'Study 歷史評估執行者' \
  historical-evaluation <id> --plan <evaluation.yml>
```

plan 包含指定 actor、frozen data_path／data_digest、authorization。authorization 的欄位同核准文件，scope 為 historical-evaluation-only，另含 candidate_freeze_digest。工具從實際事件判定階段，不依賴固定第 7／8 筆事件。資料 digest 與 session inventory 必須吻合 frozen snapshot；runner 與所有結果僅存專用 store，重算後發布 historical-evaluation-completed 及 study-terminal。第二個不同 plan 不能再次評估。相同角色的 resume 接續原 operation，無完整 runner 輸出不會自動重跑。

## JSON 介面與限制

回應固定提供 schema_version、workflow_version、study_id、authority_root、command、status；成功 result 內有操作結果與可用的 operation_id／assessment／projection。錯誤有 code、message、path、expected／actual（有具體可比較值時提供，否則為 null）、已發布事件及待恢復 journals、next_action。required_approval 為 null 表示沒有替使用者推導一份核准，實際缺件以錯誤與原 plan 為準。角色參數約束 CLI 的讀取路徑，不是作業系統身分認證。

已核准 Policy、v001 內容、真實 Studies、authority 與 evidence 不搬動、不覆寫。Lifecycle／結果定義與底層事件不變；若需要改變狀態模型，另提治理議案。
