---
name: build-strategy-study-v006
description: 為 strategy-forward-replication-research--v006 建立或接續明確指派的單一 Study，完成原生建立前檢查、Development 與合法 candidate freeze；限 study 開發者，不執行 Historical Evaluation。
---

# v006 Study 開發至凍結

固定扮演 **study 開發者**，遵守 repo `AGENTS.md`；若目前是其他角色，不自行切換。只執行明確指派的一個 Study 與已授權步驟，完成後維持 Doing，交專案管理者驗收。使用本技能不構成新的 Study 派工，也不授權正式歷史評估。

## 開始前固定範圍與版本

先讀 [操作契約](../../../workflows/strategy-forward-replication-research--v006/reference/operations.md)、[Workflow reference](../../../workflows/strategy-forward-replication-research--v006/reference/workflow-reference.md)、[最小規格](../../../workflows/strategy-forward-replication-research--v006/reference/minimal-executable-study.md) 及 [原生合成診斷](../../../workflows/strategy-forward-replication-research--v006/reference/synthetic-diagnostics.md)。新建或處理多資產時另讀 [資料契約](../../../workflows/strategy-forward-replication-research--v006/reference/multi-asset-input.md)，以實際 Schema 和程式為準；文件中的歷史 Draft 標記不替代有效 Release。

- 新 Study 使用派工時 Active 的 v006。核對 `docs/workflow-lifecycle.md`、Package 的 `release.yml`、`release-manifest.yml`、`release-test-report.yml` 及所綁定 Policy releases；透過 `validator.release.validate_release_record` 重算發布紀錄與內容清單，不只看檔案存在。Draft、Release Candidate 或有效 Release 缺漏都不能建立正式 Study；`--allow-draft` 僅用隔離 fixture，不能解開正式阻塞。
- 新 Study 的研究輸入在同名 `research/<study-id>/`。既有 Study 先核對 `workflows/strategy-forward-replication-research--v006/studies/<study-id>/manifests/workflow-reference.yml`，再讀 Source Bundle、資料或呼叫 runner。檢查 version、Package／manifest 相對路徑、resolver version、Workflow／manifest／Policy digests；禁止穿越、symlink escape（符號連結把路徑導向外部）或受限目錄。不可用 Study 內的 Workflow 副本取代 reference。
- 派工 YAML 符合 `schemas/assignment.schema.yml`，固定真實 `source_id`、指令原文或可追查摘錄、assigner、assignee、`role: study 開發者`、Study ID、`workflow_version: v006`、`scope: development-to-freeze`。使用 canonical YAML（固定鍵排序、格式與型別），可由 `validator.canonical_yaml.canonical_bytes` 產生。CLI 只核對結構，不能證明指令真偽；不能拿 example 冒充指令或補造身分、來源及研究決策。
- v006 不要求另交 Study 簽名、核准人或核准時間；既有明確授權不重問。缺少 Study 範圍、identity、研究決策或來源事實才補問；模糊的「繼續」不會擴大角色或執行範圍。

## 完整建 Study 前檢查

建第一個 event（流程紀錄）前，先備妥並固定以下研究輸入：

| 輸入 | 實際要確認的內容 |
| --- | --- |
| `preregistration.yml` | 假說、完整候選 family、maximum trials、不同且較簡單的 baseline、必要 gates（正式門檻）、research targets（研究目標）、排序與同分規則、期間、成交與成本、風險及 bootstrap 設定均明示。 |
| `candidate-definition.yml`、`qualification-spec.yml` | Study／candidate／family 一致；資格規格引用目前 preregistration 指紋，門檻與它完全一致，不能用舊檔或默認值。 |
| `development-trial-inputs.yml`、需要的 `trial-inputs/*.yml` | 唯一 Trial identity 與已登記候選相符；綁定目前 preregistration、Source Bundle、真實策略引擎和 Development procedure。 |
| `source-bundle.yml` | 列出所有會影響結果的程式、設定、相依來源及 SHA-256（內容指紋）；逐檔核對 bytes、路徑與清單指紋。資料 CSV 另行綁定，不混入此清單。 |
| `implementation-contract.yml` | 新 Study 強制使用唯一 `research/<study-id>/implementation-contract.yml`，且被 Source Bundle 綁定；明列引擎、spec／cost 常數、指標、raw／accepted 訊號、持有、冷卻、停損／停利、跳空與成交。 |
| `runner-contract.yml` | 被 Source Bundle 綁定；Development runner 與正式 procedure 是同一份，合成檢查及正式執行不能換引擎。 |
| create／Development／freeze 計畫 | 符合 `create-plan`、`development-plan`、`freeze-plan` 或 `continuous-plan` Schema；create 的 creator、development_actor 及各步驟 actor 都符合受派者。identity 明列 research_round_id、experiment_family、research_owner、historical_evaluation_operator。 |

完整 precreate 同時核對 canonical 格式、Study／candidate／Trial 身分、完整 family、來源與各引用指紋、所有影響結果的參數、validator 支援的 gates、持有／冷卻／停損／停利／跳空／指標就緒，以及原生合成 hard guard；不能拿單一子檢查取代它。新 Study 不另存第二份 manifest implementation contract。內嵌契約和同 bytes 的凍結副本僅保留既有診斷相容性，不是新 Study 的替代入口。

### 暖機與真實合成結果

暖機是指指標開始判斷前，需要累積的完整歷史 sessions（交易日）。依所有指標的最長邊界核對登記、候選、契約與引擎：SMA／ATR／Bollinger 為 min_periods−1，RSI 為 min_periods，量先行為 average_min_periods+lead_min_periods；regime 的 fast／slow 也各納入。SMA50 若含當日收盤，需要 **49 個先前 sessions**，不能沿用 25 日暖機或僅把 seed 往後移來通過。

SMA regime 必須明示 `kind: sma-comparison`、`input: Close`、`operator: '>'`、完整視窗、含當日收盤、未就緒拒絕、輸出與允許欄位，且候選與 preregistration accepted signal 一致。原生 guard 直接從人造 Close 重算長短均線和 raw／accepted 訊號，並覆蓋相等、未就緒、錯誤指標、缺 raw、無接受訊號、錯誤持有／冷卻等拒絕；不注入假的訊號欄位。

完整 `prepare` 先跑完整 native precreate，再用同一 runner 在隔離空間執行人造案例。報告須帶符合 `synthetic-report.schema.yml` 的 `native_synthetic`，同時固定 Workflow、Source Bundle、完整契約、原契約來源、引擎、spec／cost 常數與報告內容指紋。create 前與隔離 consumer 會重新產生原生結果、比對完整報告；單獨 `prepare_checks: passed`、修改後重簽的報告或其他引擎的報告都不能替代。

人造診斷的 v009 Control 直接比較，不等於派工指定的正式 baseline pipeline；檢查兩者契約與唯一差異是否符合任務。不得用 `ready_engine.py` fixture 替換研究策略或偷改假說、訊號、成本、風險與門檻來通過。`fold-warmup-too-short`、契約不支援、價格形狀無法形成真實訊號、實作違反契約或來源漂移時，依診斷分類回報；研究變更只在派工已涵蓋且尚未凍結輸入時處理，否則交由相應角色處理。原輸入不變時，重跑不會消除契約阻塞。

## 資料及執行邊界

- 只讀固定 warmup（2013 年）及 Development（2014–2018 年）資料；不得讀 quarantine（2019 年）、正式評估價格或結果。freeze 可固定 snapshot metadata／session inventory，但不打開評估 CSV。不得進入 `historical-evaluation-artifacts/`、`.super-admin/` 或非共享 `.project-manager/`。
- 計畫擇一使用單資產 `data_path`／`data_digest`，或 `data_assets`，不能混寫。新清單支援 **1–16 個資產**，按 asset_id 排序、不可重複、恰好一個 trade，其他 reference。逐檔固定 provider、symbol、repository 內 path、digest、日期、紐約時區、`available_at: after-close` 與 `interval_role: warmup-development`；與 Trial inputs 的 `data_bindings.assets` 完全一致。
- CSV 為 `Date,Open,High,Low,Close,Volume`；每份 XNYS 日期完整、嚴格遞增且與其他資產一致。缺日、重複、越界、非有限數字、非正價格或負成交量皆拒絕，不前填、插值或取交集。單檔上限 32 MiB／10000 列、總量 128 MiB。收盤後可得資料最早決定下一 session 進場；request 聲明不能取代程式與合成檢查。
- 真實 Workflow、Source Bundle、runner、CSV 與輸出只在每次 operation 的隔離暫存 workspace；永久 runtime 只留 request、runtime manifest 與 evidence 引用，`execution_workspace: temporary`。多資產在 `run/assets/<asset_id>.csv`；舊單資產在 `run/bars.csv`，不建立 `runtime/workflow/`。

## 正式命令與唯一 Trial

全域參數在子命令前，使用原 authority（保存流程核對紀錄的根目錄）：

```sh
python3 workflows/strategy-forward-replication-research--v006/operations/cli.py \
  --repository-root <repo> --authority-root <原authority> --role 'study 開發者' \
  develop-to-freeze <Study-ID> --plan <連續計畫.yml> --assignment <派工.yml>
```

連續計畫含 `create`、`development` 陣列、`freeze`，串接 prepare→create→已登記 Trial→registry→provenance→readiness→freeze；只有派工涵蓋全程且輸入齊全時才用。若只授權 Development／審閱或缺凍結事實，使用分段入口，不能為了連續執行自動補造資料。

同一 CLI 前綴的分段命令：

| 子命令 | 用法／何時停止 |
| --- | --- |
| `prepare <Study-ID> --report <報告.yml>` | 完整建立前檢查與隔離合成 runner；通過後固定此報告，不以單獨 runner-preflight 取代。 |
| `create --plan <建立計畫.yml> --report <通過的prepare報告.yml> --assignment <派工.yml>` | 不帶 Study positional argument；計畫包含 Study ID。發布三個 create 階段，不宣稱跨事件原子性。 |
| `development <Study-ID> --plan <Development計畫.yml> --assignment <派工.yml>` | 執行同一個已登記 Trial 一次，保存 candidate／baseline／inputs 與 publication 綁定。 |
| `freeze-readiness <Study-ID> --plan <freeze計畫.yml> --assignment <派工.yml>` | 暫存副本套用真實凍結規則；passed 不代表已寫 candidate freeze。 |
| `freeze <Study-ID> --plan <freeze計畫.yml> --assignment <派工.yml>` | 全部資格成立且在派工範圍內才凍結。 |
| `resume <Study-ID> --assignment <原派工.yml>` | 中斷後只接續原 operation；不另建 Study、Trial 或改 authority。 |

若派工是一個固定候選／唯一 Trial，預先登記及計畫只能保留該候選與該 Trial；不得看結果後調參、重跑或擴大家族。其他合法派工仍須遵守預先固定的 maximum trials；每個曾看結果、可能影響選擇的版本都計入完整 family 與 append-only registry（只新增不覆寫）。

## 合法凍結與交接

candidate 與 baseline 都須符合 `development-evidence.schema.yml`、`development-envelope.schema.yml`，stage=development、網路存取為 false；publication 對 Study／Trial、Source Bundle、preregistration、candidate／baseline／inputs、envelope，以及適用的資產清單 digest 完整綁定。重算正式 gates 與 research targets，分清有效證據與表現失敗：合法績效 fail 或無交易仍可能是有效研究證據；無交易不得補造統計值。

Trial-level eligible 只是局部資格。完整 freeze 還要完整 family／registry、已登記的排序與同分處理、至多一個 selected candidate、不同且較簡單 baseline、真實且有來源的 `verified-clean` provenance（資料／策略來源及正式結果接觸事實）、Source Bundle／資料／Workflow／Policy 指紋、snapshot roster 與全部 floors／drift 規則成立。研究目標失敗不能寫成 formal gate fail，但 v006 仍會拒絕該 Trial 的 freeze eligibility。缺來源用 provenance-unknown，已污染用 known-contaminated；不能自動填 clean 或強制 freeze。

不符合資格就如實記錄失敗或尚不能判斷，依授權交接；若需合法 Development 終止，僅依操作契約的 `terminate <Study-ID> --plan <合法終止計畫.yml> --assignment <派工.yml>`，不得偽造 pass 或自行延伸成正式 Evaluation／Terminal 執行。freeze 或合法 Development 終止後停止，不執行 Historical Evaluation、challenge、replay 或修改凍結策略。

開發中的 `status`／`validate` 只檢查 Development prefix；會讀流程狀態，不可用於盲檢討。遇 assignment、role、binding 或 qualification 錯誤停止核對真實缺件，不手寫 events 或用低階 API 繞過。恢復維持相同 Study／派工／連續計畫／原報告／Source Bundle／authority／operation；已完成 runner 不重跑。

交接以繁體中文列出 Study ID、派工指紋、原 authority、reference path／digest、Source Bundle、唯一或已登記 Trial／operation、正式 gates、targets、evidence validity、完整凍結資格與實際凍結佐證、未完成步驟及讀取邊界。需要盲檢討或成果卡時，依對應 v006 技能和明確任務執行，不能把本輪開發者的狀態知識說成全盲。
