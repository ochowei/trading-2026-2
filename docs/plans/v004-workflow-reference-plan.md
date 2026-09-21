# v004 Workflow Reference 化與 Study 去重計畫

本計畫用來建立 `strategy-forward-replication-research--v004`。它以 v003 的研究語意、角色分工、派工、digest、authority、immutable evidence 與一次性 Historical Evaluation 為基礎，調整 Study 如何取得 Workflow 內容，避免每個 Study 都保存一份相同的 `runtime/workflow/`。

這是建版與驗收計畫，不是 v004 的 Release Record、正式 Study 派工或 Historical Evaluation 派工。v003 與既有 Study 不搬遷、不改寫、不刪除。

## 1. 目前問題與目標

目前 v003 的 6 個 Study 共保存 844 個檔案。跨 Study 比對後，有 99 個檔案在 6 個 Study 中完全相同，約 6.77 MB，主要集中在每個 Development operation 的 `runtime/workflow/`、`uv.lock` 與相同的 `run/bars.csv`。

這些副本不是單純的 copy-forward 錯誤：v003 的 lifecycle 會把 Workflow Package 複製到 operation runtime，讓執行環境自包含。但目前的代價是：

- Workflow 的程式、validator、writer、tests、schemas、rules、政策與說明文件被每個 Study 再保存一次。
- 同一個 `workflow_digest` 的 Study 無法直接共用內容，更新共用程式時也會產生大量不必要的副本。
- Skill 不屬於 Workflow 執行結果，卻被放在 workflow package 內，造成版本套件與代理操作說明一起複製。

v004 的目標是：

1. 每個 Study 只保存明確的 Workflow reference（引用），不保存 `runtime/workflow/` 的實體副本。
2. 引用必須綁定 Workflow ID、版本、Workflow digest、release manifest digest 與 policy-set digest；不得使用 `latest`、可變 symlink 或未驗證的路徑。
3. 執行時若需要隔離工作目錄，只在暫存目錄建立副本，執行完成後不把 Workflow Package 寫回 Study。
4. v003 的既有 Study 仍依 v003 原始內容與原始 runtime 驗證；v004 不提供靜默遷移入口。
5. 新 Workflow skill 全部放在 repo 根目錄的 `.agent/skills/`，不再放進 `workflows/.../skills/`，也不列入 Workflow release digest。

## 2. 不變的治理與研究語意

以下規則從 v003 原樣保留，除非另有明確的治理決策：

- 角色仍分為超級管理者、專案管理者、Policy 管理者、workflow 維護者、workflow 執行者、study 開發者與 Study 歷史評估執行者。
- Development、blind review 與 Historical Evaluation 仍是彼此分離的操作入口；開發者不能自行切換成評估者或審查者。另保留 Development note authoring 作為只讀 Development 成果整理的輔助 skill。
- blind review 的資格獨立於 Historical Evaluation 狀態：只要沒有接觸正式結果，就可以依設計、程式與 Development 證據盲檢討；一旦讀到正式結果或 terminal，才依治理規則阻擋盲檢討。
- Study 必須有明確派工、固定的 source／plan／authority、canonical YAML 與不可覆寫的 evidence。
- `workflow_digest`、`policy_set_digest`、`source_bundle_digest`、資料 digest 與 operation digest 仍由 validator 重算，不信任 caller 自報的 pass。
- Historical Evaluation 仍只能執行一次；reservation、started、launch marker、completed、terminal 與 recovery 規則不放寬。
- v004 沒有有效 `release.yml` 前只能是 Draft 或 Release Candidate，不得建立正式 Study。
- v003 的 Workflow Package、Release Record、authority、Study、evidence 與 runtime bytes 不因 v004 建立而改變。

依據包括：[v003 README](../../workflows/strategy-forward-replication-research--v003/README.md)、[v003 操作契約](../../workflows/strategy-forward-replication-research--v003/reference/operations.md)、[v003 Development skill](../../workflows/strategy-forward-replication-research--v003/skills/build-strategy-study-v003/SKILL.md)、[v003 blind review skill](../../.agents/skills/blind-review-strategy-study-v003/SKILL.md)、[v003 Historical Evaluation skill](../../workflows/strategy-forward-replication-research--v003/skills/run-strategy-evaluation-v003/SKILL.md)、[v003 Development note skill](../../.agents/skills/study-development-note-authoring-v003/SKILL.md)、[Workflow Lifecycle](../workflow-lifecycle.md)、[自包含 Workflow Package ADR](../adr/0031-each-workflow-is-a-self-contained-package.md) 與 [Studies 位於 Workflow Package ADR](../adr/0033-store-studies-inside-their-workflow-package.md)。

## 3. v004 的引用模型

### 3.1 Study-level Workflow Reference

每個 v004 Study 建立一份不可覆寫的：

```text
studies/<study-id>/manifests/workflow-reference.yml
```

建議欄位如下：

```yaml
schema_version: 1
reference_mode: repository-workflow-package
workflow_id: strategy-forward-replication-research
workflow_version: v004
workflow_package_path: workflows/strategy-forward-replication-research--v004
workflow_digest: <sha256>
release_manifest_path: workflows/strategy-forward-replication-research--v004/release-manifest.yml
release_manifest_digest: <sha256>
policy_set_digest: <sha256>
resolver_version: 1
```

實際 schema 必須再加上安全限制：

- 路徑只能是 repository-relative、canonical、無 `..`、無 symlink escape。
- `workflow_id`、`workflow_version`、path、manifest 與 digest 必須互相一致。
- `workflow_package_path` 不得指向 `latest`、另一個 Study、`.super-admin/`、`.project-manager/` 或 `historical-evaluation-artifacts/`。
- Resolver 必須先驗證 release manifest 與 Workflow digest，再讓 runner 讀取研究資料。
- Reference 只能指向已固定的版本；修改 v004 package 後，既有 reference 必須驗證失敗，不得自動接受新內容。

`study.yml` 的 `workflow_binding` 保留既有 digest 欄位，新增 `workflow_reference_path` 與 `workflow_reference_digest`，讓 projection 與事件鏈都能追查同一份 reference。reference 是查找入口，不取代事件、authority 或 digest 驗證。

### 3.2 Operation-level Runtime Reference

每個 operation 仍保留 plan、data-access、started、completed、journal 與必要的 run evidence，但 runtime 不再保存：

```text
operations/<operation-id>/runtime/workflow/
```

改由 operation runtime manifest 保存：

```text
operations/<operation-id>/runtime/runtime-manifest.yml
```

它至少引用：

- Study-level Workflow reference 的 path 與 digest；
- source bundle 的 path 與 digest；
- runner path 與 runner digest；
- request、data 與 evidence 的 path／digest；
- resolver 與 execution contract 版本。

執行器的實際順序必須是：

```text
讀取 reference
  → 驗證 Workflow release／digest／policy
  → 驗證 source bundle／runner／plan／data digest
  → 建立暫存 execution workspace
  → 使用唯讀 Workflow Package 執行
  → 只將 runtime manifest、request、evidence 與 operation metadata 寫回 Study
```

暫存 workspace 可以為了 Python import、隔離測試或 runner 的固定相對路徑建立必要副本，但位置必須在受控暫存目錄，且不得透過 `copytree` 將 `workflow/` 留在 Study 目錄。不可用 symlink 代替 digest 驗證；symlink 只能是執行實作細節，不能成為 authority reference。

### 3.3 Source Bundle 的邊界

v004 第一階段只處理 Workflow Package 的去重，不把 Study-specific strategy source、runner、測試或 Development data 誤當成共用 Workflow。這些檔案仍依 Source Bundle digest 綁定，避免不同 Study 因共用檔名而交換內容。

可以在同一階段新增 `source-reference` 的內部抽象，讓執行器從既有 source bundle 解析檔案；但輸出必須仍能重算原始 file digest。若未完成這項抽象，先保留 Study-specific source 的現有保存方式，不以刪除檔案換取表面上的去重。

## 4. v004 Package 與 skill 位置

### 4.1 Workflow Package

建立：

```text
workflows/strategy-forward-replication-research--v004/
```

Package 保留 v003 的自包含執行內容：

```text
workflow.yml
rules/
schemas/
policies/
operations/
validator/
writer/
tests/
examples/
reference/
README.md
IMPLEMENTATION-PLAN.md
release-manifest.yml
release-test-report.yml
```

v004 Package 不建立 `skills/` 目錄。skill 是代理的操作說明，不是 Workflow 執行語意或 Study evidence，因此不列入 v004 release manifest。

### 4.2 Repo-level skills

依使用者要求，新版本 skill 放在：

```text
.agent/skills/build-strategy-study-v004/SKILL.md
.agent/skills/blind-review-strategy-study-v004/SKILL.md
.agent/skills/run-strategy-historical-evaluation-v004/SKILL.md
.agent/skills/study-development-note-authoring-v004/SKILL.md
```

這四個 skill surface 必須：

- 明確指定 v004 與角色，不自行切換角色；
- 只呼叫 v004 固定版本 CLI，不複製 validator／writer 邏輯；
- 先解析並驗證 Workflow reference，再開始任何 Study data access；
- `build-strategy-study-v004` 只處理 Development 到 candidate freeze，不能自行開始 Historical Evaluation 或 blind review；
- `blind-review-strategy-study-v004` 只處理一個指定 Study，使用研究設計、程式與 Development candidate／baseline 證據，不讀取正式 Historical Evaluation、terminal 或 `historical-evaluation-artifacts/`；blind eligibility 依實際結果暴露判定，不把「尚未執行 evaluation」誤當成唯一條件；
- `run-strategy-historical-evaluation-v004` 只接受 `historical-evaluation-to-terminal` 派工，限已 frozen candidate、只能執行一次，不能改 candidate、門檻或 Workflow reference，結果只能寫入 `historical-evaluation-artifacts/<Study-ID>/`；
- `study-development-note-authoring-v004` 只整理 300–600 字的 Development 成果卡，不讀正式結果、不改 Study lifecycle、不取代 blind review 或 Historical Evaluation；
- 不讀取不符合目前角色範圍的 evaluation store、`.super-admin/` 或 `.project-manager/` 專屬資料；
- 交接時回報 Study ID、v004、reference digest、authority root、事件 head、operation ID 與缺件。

v003 既有 skill 不改寫；它們繼續只服務 v003。若實際 skill loader 只掃描 `.agents/` 而不掃描 `.agent/`，必須在實作前建立可驗證的載入規則；不能未經決定把使用者指定的 `.agent/` 靜默改成 `.agents/`。

## 5. 程式調整範圍

### 第一層：Reference Resolver

新增一個只負責解析與驗證引用的共用模組，例如：

```text
validator/workflow_reference.py
```

它負責：

1. 讀取 canonical `workflow-reference.yml`。
2. 安全解析 repository-relative path。
3. 驗證 `workflow.yml`、schemas、rules、policies、maintained implementation files 與 release manifest 的 digest。
4. 驗證 release record 與 reference 的版本、manifest digest、Workflow digest、policy digest。
5. 回傳唯讀 package root 與可供 validator／runner 使用的明確 context。
6. 在 path traversal、symlink escape、版本不符、digest 漂移、release 缺失或 reference 指向另一個 Study 時拒絕。

### 第二層：Lifecycle 與 Evaluation

調整 v003 對應實作：

- `operations/lifecycle.py`：不再把 `service.workflow_root` 複製到持久化的 `runtime/workflow/`；改寫入 runtime manifest，並使用暫存 execution workspace。
- `operations/evaluation.py`：正式 Historical Evaluation 同樣從 reference resolver 取得 Workflow；評估結果仍只寫 `historical-evaluation-artifacts/<Study-ID>/`。
- `operations/preflight.py`：合成 preflight 驗證 reference resolver 與正式 runner 使用同一套路徑解析，不因 fixture 另走寬鬆路徑。
- `operations/launch.py`：明確區分 repository root、Workflow package root、temporary execution root 與 data root，避免把任一個模糊 root 當成全部權限。
- `operations/service.py`、`writer/service.py`：建立、recover、status、validate 與 append event 都重驗 reference path／digest；不能只信任 `study.yml` projection。

### 第三層：Schema、validator 與 release manifest

新增或調整：

- `schemas/workflow-reference.schema.yml`；
- `schemas/runtime-manifest.schema.yml`；
- `schemas/study.schema.yml` 或等價 Study binding schema；
- `schemas/source-bundle.schema.yml` 的禁止嵌入 Workflow 規則；
- `validator/paths.py` 的 reference 與 symlink 安全檢查；
- `validator/release.py` 的 reference／release／digest 一致性檢查；
- `validator/study.py` 的 Study binding、operation runtime 與 recovery 驗證；
- `release-manifest.yml` 的新 schema、resolver、lifecycle、CLI 與測試檔案。

v004 的 validator 應明確拒絕把下列內容當成合法的 Workflow reference：

- `runtime/workflow/` 實體副本；
- `workflow_path: latest`；
- 沒有 digest 的相對路徑；
- 指向另一個 Workflow version、另一個 Study 或工作樹外部的 path；
- 只有 `study.yml` 文字欄位、但沒有不可覆寫 reference artifact 的 binding。

## 6. 實作階段與順序

| 階段 | 工作 | 完成條件 |
| --- | --- | --- |
| 1. 建立 v004 Draft | 從 v003 複製 Workflow 執行內容，但排除 `studies/` 與 `skills/`；版本、package path、文件與 schema 改為 v004 | v003 工作樹與既有 Study bytes 沒有變化；v004 尚無 `release.yml` |
| 2. 固定 reference 契約 | 新增 workflow/reference、runtime manifest、resolver schema 與安全 path 規則 | 正常 reference、錯版、漂移、path traversal、symlink escape、無 release 均有明確結果 |
| 3. 改 lifecycle／runner | 讓 Development 與 Evaluation 使用 reference；暫存副本不落在 Study | 新建 fixture Study 沒有 `runtime/workflow/`，仍能完成 runner、evidence 與 recovery |
| 4. 改 validator／writer | 讓低階 writer、status、validate、recover 都重驗同一份 reference | 不能靠手動改 `study.yml` 或 runtime manifest 繞過 digest／release 檢查 |
| 5. 建立 v004 skills | 在 `.agent/skills/` 寫 Development、blind review、Historical Evaluation 與 Development note skill；Workflow Package 不放 skill | 四個 skill 只呼叫固定 v004 CLI；角色邊界、盲檢討隔離與資料讀取限制有測試 |
| 6. 相容性回歸 | 用現有 v003 fixture 驗證 v003 不被新 resolver 或共用模組污染；用 v004 fixture 驗證 reference mode | v003 既有驗證通過；v004 不會誤接受 v003 runtime layout |
| 7. Release Candidate | 產生 v004 manifest、test report，執行完整測試、Ruff、canonical／schema／policy／failure recovery 檢查 | 所有結果可重現，交給 Trusted Approver；不由實作者建立正式 `release.yml` |
| 8. 發布後治理 | Trusted Approver 建立 v004 Release；再更新 Workflow Lifecycle，讓 v003 停止接受新 Study | v003 既有 Study 仍可讀、驗證、完成；新 Study 才使用 v004 |

## 7. 必要驗收案例

### Reference 與去重

- 新 v004 Study 可以由 reference 找到同一份 v004 Workflow Package。
- 兩個 Study 使用相同 reference 時，不會各自建立 `runtime/workflow/`。
- `runtime-manifest.yml` 的 Workflow、source、runner、request、data digest 任一漂移都會拒絕。
- 修改、刪除或替換 Workflow Package 後，既有 Study 的 `validate` 會明確回報 digest／release mismatch。
- `latest`、`..`、絕對路徑、外部 symlink、跨 Study path 與受限目錄均在讀取資料前被拒絕。
- 暫存 execution workspace 中斷後不會在 Study 留下半份 Workflow copy；相同 operation 可依 v003 的 recovery 語意安全接續或判定 evidence unavailable。

### Study lifecycle 與角色

- 沒有 Workflow Release 時，正式 `create` 仍拒絕；`--allow-draft` 只能用於隔離測試。
- 開發者只能執行 Development-to-freeze；不能因 reference 已驗證就執行 Historical Evaluation。
- blind reviewer 只能讀取設計、程式與 Development candidate／baseline 證據；正式結果、terminal 或 `historical-evaluation-artifacts/` 一律不可讀取。
- blind review 不以「Historical Evaluation 尚未開始」作為唯一資格；若已實際接觸正式結果，必須拒絕盲檢討；若未接觸正式結果，則可依獨立的 blind-review 規則判定資格。
- Evaluation operator 只能使用已 frozen candidate、原 reference、原 source、原 plan 與原派工；不能換 Workflow version 取得第二次評估。
- Development note author 只能使用 Development 證據撰寫成果卡，不得把 note 當成盲檢討、正式評估或 Study 狀態變更。
- `status`、`validate`、錯誤訊息與恢復流程不能越過角色範圍讀取 evaluation store 或管理者專屬資料。

### 相容性與完整性

- v003 的 workflow digest、release record、Study event chain、authority checkpoint、runtime 與 evidence 完全不修改。
- v003 validator 仍能驗證 v003 Study；v004 validator 不會把 v003 Study 靜默升級成 v004。
- v004 的 source bundle 仍能驗證每個 strategy engine、procedure、runner、test 與輸入 digest；不把 Workflow Package 偷塞進 Study-specific bundle。
- v004 package 的 `release-manifest.yml` 不包含 `.agent/` skill，skill 變更不會偷偷改變 Workflow digest。
- 所有新測試使用暫存目錄與合成資料，不讀取正式 Historical Evaluation 結果，也不寫入正式 authority 或 artifact store。

## 8. 發布、遷移與回復策略

1. v004 在 Draft／RC 階段可以使用複製的 v003 Study fixture，但 fixture 不得寫回正式 `studies/`。
2. v004 Release 前，v003 仍維持 Active，新的 v003 Study 仍可依現行流程建立；不得在 v003 內偷偷套用 reference mode。
3. v004 Release 後，依 Workflow Lifecycle 將 v003 標記為 Superseded，停止接受新的 v003 Study；v003 既有 Study 保持原版。
4. 不把 v003 Study 直接轉換成 v004。若研究必須使用 v004，建立新的 v004 Study，重新保存研究 identity、派工、source／provenance 事實與 reference binding；不能以複製 `study.yml` 或改版本欄位完成遷移。
5. 不刪除既有 v003 `runtime/workflow/`。若日後建立專用內容定址儲存，先新增可驗證的 immutable object 與 resolver，再考慮是否有受治理的封存方案；不以手動刪檔減少大小。

## 9. 交付物

- v004 Draft Workflow Package；
- `workflow-reference.schema.yml`、`runtime-manifest.schema.yml` 與對應 validator／writer／resolver；
- 不再持久化 `runtime/workflow/` 的 lifecycle、preflight、evaluation 與 launch 實作；
- v004 測試、合成 fixture、failure／recovery 回歸案例、release manifest 與 test report；
- `.agent/skills/build-strategy-study-v004/SKILL.md`；
- `.agent/skills/blind-review-strategy-study-v004/SKILL.md`；
- `.agent/skills/run-strategy-historical-evaluation-v004/SKILL.md`；
- `.agent/skills/study-development-note-authoring-v004/SKILL.md`；
- v004 README、操作指南、reference 契約與去重限制說明；
- v003 相容性驗證結果；
- 提交給 Trusted Approver 的 Release Candidate 摘要。

## 10. 明確不在本計畫內

- 不修改 v003 或 v002 的任何已發布內容。
- 不刪除既有 Study、runtime、journal、evidence、authority 或 evaluation artifact。
- 不執行正式 Historical Evaluation。
- 不更換研究目的、資料日期、candidate eligibility、policy 語意或 terminal 結果定義。
- 不把 skill 當成權限系統，也不以 skill 取代 validator、writer、release digest 或 Workflow approval。
- 不在本計畫內建立 v004 `release.yml`；那是 Trusted Approver 在 Release Candidate 驗收後的獨立動作。
