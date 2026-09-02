# 策略前瞻驗證流程 v011：現行做法說明

## 文件定位

本文件以繁體中文說明目前生效的
`strategy-forward-replication-research@v011` 實際如何運作，供研究負責人、執行者、審查者與
維護者快速理解流程。

本文件是**說明性指南**，不是 workflow 行為權威。若本文與下列來源不一致，應停止操作並以
較高順位來源為準：

1. repository guardrails；
2. `workflows/strategy-forward-replication-research--v011/WORKFLOW.md`；
3. v011 release 所固定的 normative dependencies；
4. 本文件。

截至 `2026-09-02`，v011 已完成獨立 release preparation 與 Workflow Release Activation，root
registry 狀態為 `active`。動態 control state、study 狀態與 safety assessment 仍應在操作當下重新
查詢，不應只依賴本文的日期。

## 一句話說明

這套流程把一個日線策略鎖定在固定的歷史日曆中：只用 `2014-2018` 的 Development 證據選出
唯一候選，接著以 `2020-2024` Historical Evaluation、九項穩健性挑戰與 `2025` 歷史成交重播，
產生可重播、可跨 study 比較，但**不具任何實盤或 promotion 權限**的研究結論。

## 最重要的權限邊界

v011 只有 `fixed-calendar-retrospective` route。所有 outcome windows 在 study 建立時都已經結束，
因此它不是前瞻 Shadow，也不能因為換一位研究者、建立新 study 或承諾不再查看舊結果，就重新
取得 unseen／prospective 身分。

即使所有 gate 都通過，正向結果也只能是：

```text
pass + retrospectively-supported
```

它不會產生：

- `shadow-eligible` 或 `activation-eligible`；
- strategy activation、Controlled Activation 或 Active 狀態；
- broker、order、position 或 live trading authority；
- 可直接交給 followup 建立新部位的資格。

Workflow Release Activation 只表示 **workflow version 成為 repository 的有效治理規則**，不表示
任何策略獲准啟用。

## 固定研究日曆

每個合格 study 都使用同一組由 workflow 擁有的 civil-date boundaries：

| 資料角色 | 固定日期 | 用途 |
|---|---|---|
| Warmup-only | `2013-01-01` 至 `2013-12-31` | 只供指標前置觀察，不計入績效 |
| Development | `2014-01-01` 至 `2018-12-31` | 研究、比較與選出候選 |
| Quarantine | `2019-01-01` 至 `2019-12-31` | 隔離區間，不得移入其他角色 |
| Historical Evaluation | `2020-01-01` 至 `2024-12-31` | 五個互不重疊的年度 folds |
| Retrospective execution replay | `2025-01-01` 至 `2025-12-31` | 固定歷史成交重播 |

Planner 會依 pinned market/session policy 推導每個角色的 exact session inventory。Caller 不得自訂
日期、縮短區間、換年份、漏掉 session、加入額外 session 或讓角色重疊。缺少完整歷史的資產不具
資格。

Warmup session、carry-in position 或 fold 外的 exit 都不能貢獻 Evaluation 或 replay 的 signal、
position、fill、cooldown、損益、資本或 metrics。

## 角色與權限分工

| 角色 | 主要責任 | 不得做的事 |
|---|---|---|
| Human workflow release approver | 分別核准 release preparation 與 workflow activation | 把 release 當成策略實盤核准 |
| Human research owner | 核准 preregistration、Development、candidate freeze 與 stage advancement | 覆寫 gate、隱藏 trial、事後放寬規則 |
| Researcher／Agent | 草擬計畫、在 Development 內研究、執行已授權工作並整理 evidence | 自行核准晉級、先看後段 outcome 再改候選 |
| Automated verifier／evidence systems | 從 immutable inputs 重算 identity、metrics 與 gates | 接受 caller 自報的 passed flag 取代重算 |
| Historical replay operator | 執行固定 2025 provider-free paper replay | 接觸 broker、建立真實部位或 actionable order |
| Independent reviewer | 依 frozen plan 與完整 evidence 獨立判定 outcome | 修補 evidence、調參或創造 disposition |
| Shared-state migration approver | 核准完整 registry/checkpoint inventory 與 repository identity | 忽略已發現 chain 或把 migration 當成 plan closure |
| Plan administration approver | 逐案核准合格 plan 的 abandonment／cross-chain closure | 把行政 closure 當成 study outcome |

每個人工核准都必須使用穩定識別碼並記錄真實的當下時間。人類核准與系統 gate 缺一不可；人工
不能把 `fail` 或 `indeterminate` 改成 `pass`。

## 開始前必須具備的條件

在任何 outcome-relevant Development、plan registration、screen、challenge、replay 或 terminal
review 前，至少要完成：

1. 指定 experiment family、唯一 research-round identity、人類 research owner 與 replay operator。
2. 使用位於 `src/trading/research_definitions/` 的 workflow-native research definition；不得就地
   改寫 closed legacy experiment identity。
3. 準備可驗證的 market-data snapshot、definition snapshot、trial registry 與 exact policy-set
   identity。
4. 在查看正式 Evaluation／replay outcome 前，完成 asset-specific provenance audit，並凍結為
   `verified-clean`、`known-contaminated` 或 `provenance-unknown`。缺少證明時一律使用
   `provenance-unknown`。
5. 預先註冊可否證假說、trial budget、完整候選集合、selection rule、distinct family baseline、
   成交與持有規則、base／stress costs、風險上限、九項 challenge contracts、門檻、pause／recovery
   與 outcome rules。
6. 凍結 structured `QUALIFICATION_SPEC.json`；它必須完整描述 route、calendar、session roles、
   source digests、policy set、成本、seeds、rounding、tie handling、challenge algorithms、raw evidence
   與 failure conditions，不得依賴 implicit defaults。
7. 先完成 v011 shared qualification state 的 verified migration，並證明完整 source inventory、
   catalog、全部 immutable shards/checkpoints、active chain/head、shared locks 與 journal 一致。

任何 identity 缺失、digest drift、implicit latest、stale／legacy result 冒充 current evidence，或
shared-state authority 不完整，都必須 fail closed。

## 主流程

```text
規劃與預註冊
  -> Development 授權與研究
  -> 候選凍結
  -> 固定日曆 readiness／qualification plan
  -> 2020-2024 Historical Evaluation + 九項 challenges
  -> 2025 retrospective execution replay
  -> 獨立 terminal review
  -> pass／fail／indeterminate
```

### 1. 規劃與預註冊

Study 必須建立在 exact active v011 下，route 固定為 `fixed-calendar-retrospective`。Preregistration
會固定研究假說、最大 trials、完整 family、候選選擇方法、成本、風險、calendar、所有 gate 與
evidence requirements。

Selection history 若不完整，必須如實披露且不得回填。Retrospective selection boundary 只能記錄
真實的當下時間，不能偽裝成歷史上的 Forward Selection Epoch。

### 2. Development 與候選凍結

Development 階段可修改 signal、parameter、entry、exit 與 execution assumptions，但只能使用
Development evidence。每個曾查看結果、且可能影響選擇的 outcome-relevant semantic definition，
都算一個 trial；失敗、移除與放棄的版本也不能從 history 消失。

正式執行 Development 前，另需 add-only `DEVELOPMENT_AUTHORIZATION.json`。最後依預註冊規則：

1. 先排除不符合 eligibility 或 risk conditions 的候選；
2. 以 canonical sleeve 的 base-net daily-equity Sharpe 由高至低排序；
3. 完全同分時依預註冊的穩定 trial ID 排序；
4. 選出至多一個 candidate 與一個不同的、較簡單的 family baseline。

任何應納入候選無法驗證時，不得產生 partial ranking。達到 `maximum_trials` 仍沒有合格候選，
本輪即終止。

`CANDIDATE_FREEZE.json` 不可手寫。Selection input 只提供 selected candidate、distinct baseline
與 ordered complete family；guarded writer 會加入 exact digests、approval、current time、narrow
scope 與 trial budget，並 add-only 保存。Freeze 後禁止 tuning、reranking、擴大家族或更換候選。

### 3. Fixed-calendar readiness 與 plan registration

Provider-free exact-study compiler 會從 released workflow、preregistration、PLAN、qualification
spec、Development authorization、candidate freeze、policy releases、complete family 與 fixed
calendar 重建全部 frozen facts。

Complete-family register-only preparation 與 qualification-plan append 是同一個可恢復的 logical
transaction。它會：

- 使用真實當下時間配置缺少的 outcome-free trial registrations；
- 在 shared lock 內驗證 complete family 與 single-open-plan constraint；
- 以 write-ahead journal 綁定 exact study、registries、approver、污染聲明與全部 prepared bytes；
- 只允許相同 commit decision 的 idempotent recovery。

Dry-run 不得寫 registry、建立 observation、執行 strategy definition 或讀取 market outcome。

### 4. 固定 Historical Evaluation 與九項挑戰

Evaluation 僅使用 `2020-2024` 五個 annual folds。Formal observations 必須使用 immutable snapshots
與 offline runs；每筆交易依 signal date 歸屬，並在同一 fold 內退出。

必要挑戰共九類：

1. 現金基準；
2. 不同且較簡單的 family baseline；
3. exposure-matched 隨機進場；
4. 預註冊的小幅參數擾動；
5. 延後進場；
6. 較高成本；
7. 較差成交；
8. 漏單；
9. 市場 regime 檢查。

每項 challenge 都要有 typed gate、exact target、registered implementation、唯一 evidence identity
與獨立 immutable artifact。Guarded challenge-only operation 必須 provider-free，且不能呼叫 provider、
refresh、screen coordinator、research execution、registry writer、terminal review 或 study transition。

九個 artifacts 與 manifest 必須 atomic publish；相同 retry 可 idempotent recovery，不完整、衝突或
不同 binding 的 publication 一律 fail closed。

### 5. 固定 2025 歷史成交重播

只有已保存且通過的 Historical Evaluation 才可進入 replay。它必須綁定同一 study、freeze、plan、
policy set、data generation 與完整 2025 session inventory，並以 provider-free 方式依 session 順序
產生：

- non-actionable paper proposals；
- canonical simulated fills；
- position、cash 與 ledger events；
- base／stress metrics；
- checkpoint prefixes；
- historical drift assessment。

這些都是歷史模擬 evidence，不是 Shadow。Operation 不得產生 broker fills、actual positions、
orders 或 new-entry authority。

### 6. 獨立 terminal review

`TERMINAL_EVIDENCE.json` 必須綁定 preregistration、spec、Development authorization、candidate
freeze、plan、Evaluation、九項 challenges、2025 replay、authoritative registry snapshot/head、exact
workflow/policies、complete commit SHA 與全部 required digests。

Independent reviewer 必須從 authority evidence 重算結果，不信任 caller 或 manifest 自報的
passed flag，也不得在 review 時補資料、改門檻或調整策略。

## 不可放寬的最低門檻

Study 可以在 outcome 前設定更嚴格的 gate，但不能低於下列 floor：

| Gate | 最低要求 |
|---|---|
| Development coverage | 固定 `2014-2018` 五個完整年度，另含 2013 warmup |
| Historical Evaluation | 固定 `2020-2024` 五個完整且互不重疊的 annual folds |
| Historical completed trades | 至少 20 筆 |
| Traded folds | 至少 3 個 |
| Positive traded folds | 至少 60% |
| Base return／profit factor | compounded return > 0；profit factor > 1.1 |
| Stress return／profit factor | return > 0；profit factor > 1 |
| Stress drawdown | 不得突破 preregistered 上限 |
| Fold concentration | 任一 fold 不得超過總交易或總正獲利的 50% |
| Selection adjustment | complete-family family-wise confidence 至少 90% |
| 2025 replay coverage／fills | 涵蓋全部預期 sessions；至少 12 筆 completed simulated fills |
| 2025 replay performance | base／stress return > 0、profit factor > 1、stress drawdown 合規，且 historical critical-drift replay 通過 |

Evaluation 或 replay 的任一完整 frozen gate 失敗，都會終止本 study，不得換資料、換年份、延長
期間或降低門檻後重試。

## Outcome 如何解讀

| Outcome | v011 的意思 | 後續權限 |
|---|---|---|
| `pass` | 全部必要 identity、approval、coverage、Evaluation、challenge 與 replay gates 通過 | 只得到 `retrospectively-supported` |
| `fail` | 任一可判定 frozen gate 失敗，或 Development 在 trial budget 內找不到候選 | 本輪停止，不得重用相同 evidence 冒充獨立驗證 |
| `insufficient-evidence` | v011 不允許；所有時間窗都已結束 | 樣本或 fills 不足直接是 `fail` |
| `indeterminate` | identity、資料、artifact、approval、provenance 或 integrity 不足以可信判定 | 暫停晉級，只能恢復同一 frozen evidence |

`historical_plan_abandoned` 與 `historical_plan_closed_invalidated` 是行政 terminal facts，不是 study
outcome，也不能用作 Evaluation evidence。

## Shared qualification state：v011 的核心變更

Frozen study 仍把 `state/qualification-registry.json` 當作 repository-relative logical identity，
但這不代表每個 worktree 各自建立一份 mutable registry。Runtime 必須從 verified Git common
repository identity 解析出唯一的 private shared authority，包括：

- immutable content-addressed historical registry shards 與 exact checkpoints；
- append-only authority catalog；
- 唯一 active registry chain 與 head checkpoint；
- shared mutation／study-registration locks；
- recoverable transaction journal。

所有 worktrees 必須看到相同的 catalog、chains、global family open-plan projection 與 locks。Branch、
commit 新舊、檔案時間、worktree path 或 caller assertion 都不能選出「較新的」registry 作 winner。

Migration 必須列出完整 source registry/checkpoint inventory，先 preview，再由人類核准綁定 exact
bytes 的 decision 後 apply。Imported shards 永不重寫、拼接、刪除或重新 hash；後續事件只能 append
到 active chain。發現任何未註冊 registry、missing checkpoint、chain conflict 或 pending journal，
全部 qualification mutation 都要暫停。

Tracked qualification evidence 必須自包含 catalog、所有 referenced shards/checkpoints、active
chain/head 與 exact digests，使 fresh clone 能 provider-free review，但 tracked snapshot 不會反向
授權 private mutation。

## 主流程外的兩種行政操作

### Cancelled study 的 plan abandonment

只有 exact-study-bound、尚未 screen、尚未 abandonment，且 owning study 已是 terminal
`cancelled` 的 open plan 才符合資格。每次操作都要以當下 human approval 與具體 reason，透過
active/effective v011 的 `qualification-plan-abandonment-v1` capability append 唯一 terminal event。

Study cancellation 本身不會關閉 plan；plan abandonment 也不會改寫、恢復、完成或評估 study。

### Superseded workflow 的 cross-chain invalidated closure

Paused study 只有在 owning workflow 已 superseded，且 accepted version-impact evidence 明確指定
exact `close-invalidated` 時，才能另取當下核准，在 shared active chain append
`historical_plan_closed_invalidated`。這個事件只關閉 administrative family lock，不會 cancel、
complete、move、resume、review 或替 study 指定 outcome。

Migration、plan closure、study operation、terminal review、workflow release／activation 與 trading
authority 都是彼此獨立的 authority seam，不得互相推定。

## Evidence 與保存位置

| 類型 | Canonical location／identity |
|---|---|
| Workflow-native trial artifacts | `results/research-trials/<family>/<trial>/` |
| Workflow study evidence | `results/workflows/<workflow>--vNNN/<study>/<stage>/` |
| Pre-freeze research evidence | `results/evidence/research/<sha256>.md` |
| Qualification evidence snapshots | `results/evidence/qualification/<sha256>.json` |
| Trial／path registries | `results/registries/` |
| Retired legacy results | 唯讀 `legacy/results/<experiment>/` |
| Mutable shared qualification authority | verified Git-common private runtime root；不得 commit |

Formal result 必須在查看 strategy output 前保存 `metadata.observation_provenance`，包含 canonical
argv、exact workflow/release digests、policy set、definition/data manifests、complete Git HEAD，以及
決定 workflow binding 或 publication 的 maintained orchestration source bytes 與 SHA-256。

Evidence 一旦被 immutable artifact 以 digest 引用，就不得覆寫、刪除、改名或改用 mutable
`latest` pointer 取代。`workflows/` 不得存放 raw private trading data、broker exports、credentials、
個人持倉或 private ledger。

## v011 固定的 policy releases

| Policy family | Version |
|---|---|
| `us-equity-market` | `v002` |
| `firstrade-manual-trading` | `v001` |
| `canonical-execution` | `v001` |
| `portfolio-risk` | `v001` |

正式執行必須解析 exact release digests 與 composite policy-set identity，不能使用 implicit latest，
也不能在 workflow 或 study 內自行覆寫 selected policy configuration。

## Pause、recovery 與終止

遇到資料、calendar/session inventory、snapshot、policy binding、registry、shared catalog、lock、
journal、publication 或 evidence-integrity 問題時，立即 pause advancement 或全部 qualification
mutation。

Recovery 只能修復同一 frozen definition、calendar、manifests、thresholds 與 publication decision，
或完成 inputs 完全相同的 idempotent transaction。不能新增 sessions、延長 2025、換 data generation、
改 threshold、刪 event 或人工 override。

以下情況會終止本輪：

- trial budget 用盡且沒有 candidate；
- Evaluation 或 replay `fail`；
- candidate freeze 後發生 outcome-relevant definition change；
- required evidence 無法恢復；
- human research owner 明確停止。

另開 study 仍然使用 v011 的同一固定 calendar，並須如實揭露所有先前 outcome exposure；不能把
重跑說成新的 clean 或 prospective evidence。

## 日常判斷清單

在執行任何 outcome-relevant 動作前，至少確認：

- exact workflow path 是 registry 中的 `active` v011，而不是只看 `RELEASE.json` 是否存在；
- exact-version control state 沒有 invalid／indeterminate conflict 或 open safety assessment；
- study lifecycle 與 requested transition 相容，且需要的人類核准是本次、當下、具穩定 identity；
- shared qualification migration 已完成，catalog、shards、active chain/head、locks 與 journal 完整；
- preregistration、spec、Development authorization、freeze、plan 與 policy digests 全部一致；
- calendar/session inventories 完整、互斥，且沒有 role leakage；
- operation 的 dry-run 真正零 mutation；
- evidence destination、digest、Git tracked/local-only boundary 與 atomic publication 規則正確；
- 結果將被標記為 retrospective，且不會流向 broker、order、new-entry 或 live authority。

## 延伸閱讀

- 行為權威：`workflows/strategy-forward-replication-research--v011/WORKFLOW.md`
- Version metadata：`workflows/strategy-forward-replication-research--v011/README.md`
- Shared qualification authority：`docs/shared-qualification-state-v011.md`
- 固定日曆與 challenge/replay contract：`docs/historical-qualification-and-shadow-v009.md`
- Plan abandonment：`docs/historical-qualification-and-shadow-v010.md`
- Result namespaces：`docs/result-storage-layout-v009.md`
- Legacy retirement：`docs/legacy-experiment-retirement-v010.md`
- Workflow lifecycle registry：`workflows/README.md`

