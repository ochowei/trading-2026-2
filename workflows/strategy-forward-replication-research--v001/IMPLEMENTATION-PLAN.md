# Strategy Forward Replication Research v001 修復計畫

狀態：implemented，release candidate 等待 trusted approver
交付目標：release candidate，不建立 `release.yml`

實作結果：validator、guarded writer、local authority store、canonical YAML、四份本地 policy releases、完整事件流程、反例 tests、文件、release manifest 與 test report 均已建立。正式啟用仍刻意保留給 trusted approver，故本次沒有建立 `release.yml`。

## 目標

把目前偏向文字說明的 `workflow.yml`，改造成一個自包含、可執行、可重算且不容易誤用的 Workflow Package。完成後，任何 Study 都只能依固定順序新增事件；validator 會從 raw evidence 重算結果，不接受呼叫者自行填寫的 `pass`。

本計畫只處理 `strategy-forward-replication-research--v001`。未來 workflow 可以採完全不同的資料結構、事件、階段與結果，不必繼承本 workflow 的模型。

## 已確認的設計邊界

- 所有正式檔案使用 repository-canonical YAML。
- Workflow definition 與 Study runtime 都位於同一 Workflow Package，但 Workflow digest 永遠排除 `studies/`。
- Study Events 是狀態的唯一事實來源；`study.yml` 只是可重建的摘要。
- 正式寫入只經過 guarded writer。
- 不依賴 Git；Git 只可作為選用的備份與 review 工具。
- 使用簡化的本機 append-only authority store，只防誤操作與意外回退，不防惡意檔案管理者。
- 信任檔案填寫者，不使用數位簽章。
- Independent Review 指使用 frozen inputs 與 raw evidence 重新計算；同一人可以兼任所有角色。
- 外部 runner 產生 signals、trades、fills 與 ledger；本專案負責治理、驗證與 metrics 重算，不重建完整策略引擎。
- 最終只交付 release candidate；必須另經 trusted approver 核准才能建立 `release.yml`。

詳細理由記錄於 repository 根目錄的 `CONTEXT.md` 與 `docs/adr/`。

## 不在本次範圍

- 任意策略的 signal engine。
- 九項 challenges 的完整資料產生器。
- 真實券商連線、下單或部位管理。
- Trailing stop、stop-limit 或其他未允許的 Proposal Order Types。
- 數位簽章、金鑰管理、WORM storage 或外部 transparency log。
- 共同 workflow framework、共同 state machine 或第三方 plugin 系統。
- 自動建立 `release.yml` 或自行啟用 v001。

## 目標目錄

```text
workflows/strategy-forward-replication-research--v001/
├── workflow.yml
├── release-manifest.yml                 # 最後階段產生
├── IMPLEMENTATION-PLAN.md
├── schemas/
├── rules/
├── policies/
│   ├── us-equity-market--v002/
│   ├── canonical-execution--v001/
│   ├── portfolio-risk--v001/
│   └── paper-proposal-orders--v001/
├── validator/
├── writer/
├── tests/
├── examples/
├── reference/
└── studies/
    └── <study-id>/
        ├── events/
        ├── evidence/
        ├── manifests/
        ├── journals/
        └── study.yml                    # 可重建 projection
```

大型或敏感 artifacts 不放在 Workflow Package，改存外部 content-addressed storage；Study 只保存 Evidence Manifest。

## 階段 1：重寫 v001 的權威規格

### 工作

1. 將 `workflow.yml` 改為自包含的 v001 definition：
   - 加入明確 `workflow_version: v001`。
   - 移除會被直接修改的 `status`。
   - 移除必要的 `exact_git_commit`，改用 `source_bundle_digest`。
   - 把合法階段、提前終止路徑、outcomes 與 recovery 寫成可供 validator 使用的資料。
   - 把 Workflow Floors 寫進正式 definition，不再只存在 guide。
   - 明確綁定四份 vendored policy releases 與 digests。
2. 把 manifest 內的 mutable status 模型改成 Study Events 加 projection。
3. 明確定義 provenance：
   - `verified-clean` 可以繼續。
   - `known-contaminated` 終止為 `fail`。
   - `provenance-unknown` 終止為 `indeterminate`。
4. 明確定義 `fail`、`indeterminate`、`paused` 與 recovery。
5. 將 failure policy 擴大到 Development eligibility、candidate freeze、Evaluation、九項 challenges、Replay 與 review integrity。

### 交付物

- 新版 `workflow.yml`。
- `rules/state-machine.yml`。
- `rules/workflow-floors.yml`。
- `rules/evidence-requirements.yml`。
- `rules/failure-and-recovery.yml`。

### 完成條件

- 規格中不存在 `pending → frozen/pass` 必須覆寫 immutable fact 的矛盾。
- 每個 terminal outcome 都能追溯到一條合法 event path。
- 沒有完成 review recomputation event 時，不可能形成 `pass`。

## 階段 2：Canonical YAML 與 schemas

### 工作

1. 新增 `jsonschema` dependency；schema 本身以 YAML 表示。
2. 實作 repository-canonical YAML profile：
   - UTF-8、LF、兩格縮排、固定 key 排序。
   - 日期、小數與 digests 使用字串。
   - 禁止 anchors、aliases、自訂 tags 與 comments。
   - 檔尾恰好一個換行。
   - validator 重新序列化後必須和原 bytes 完全一致。
3. 建立 schemas：
   - workflow definition、policy release 與 release manifest。
   - event envelope 和每種 event payload。
   - preregistration、Trial、Candidate Freeze、Data Snapshot、Evidence Manifest。
   - Evaluation、Challenge Evidence、Replay、Terminal Evidence 與 Study projection。
4. 統一 SHA-256 表示法為 64 個小寫十六進位字元。
5. repository-relative paths 必須正規化，禁止絕對路徑、`..`、symlink escape 與 mutable `latest` pointer。

### 交付物

- `schemas/*.schema.yml`。
- `validator/canonical_yaml.py`。
- `validator/schema_validation.py`。
- canonical YAML golden fixtures。

### 完成條件

- 相同資料結構只會產生一種正式 YAML bytes。
- 非 canonical、路徑逃逸或格式錯誤的 artifact 會在進入語意驗證前被拒絕。

## 階段 3：移植並重新發布 policies

來源：`/Users/william/gitRepo/trading-2026-1/policies/`。

### 工作

1. 移植 `us-equity-market v002` 的規則值：
   - Yahoo、日線、auto-adjusted、XNYS。
   - 收盤後 30 分鐘 decision buffer。
   - 未知 publication time 至少延遲一個 session。
   - excess lag 預設 fail。
   - formal runs 只能讀 frozen snapshots，不能連線 provider。
2. 移植 `canonical-execution v001`：
   - next-open market entry。
   - day limit target。
   - GTC stop-market。
   - next-open expiry。
   - intrabar ambiguity 採 adverse stop first。
   - missing next session 視為 unfilled。
   - Base costs：進出各 5 bps slippage，每邊 1 bps fee。
   - Stress costs：進出各 20 bps slippage，每邊 2 bps fee。
3. 移植 `portfolio-risk v001`：
   - equal isolated sleeves。
   - 每 sleeve 最多一個持倉、禁止加碼與跨 sleeve 借款。
   - Evaluation 不 rebalance。
   - preregistration 後 allocation 不得修改；要修改只能開新 Study。
4. 不移植 Firstrade broker authority，改建 `paper-proposal-orders v001`：
   - 只允許 `MARKET`、`LIMIT`、`STOP_MARKET`。
   - 拒絕 trailing stop、stop-limit、trailing stop-limit 與未登記種類。
   - 所有輸出都是 non-actionable Proposal。
5. 每份 policy 重新建立 canonical YAML release metadata、本地 implementation bindings、conformance tests 與新 digests。

### 完成條件

- Workflow 不引用原專案的 `RELEASE.json` 或不存在的實作 digest。
- 四份 policies 可以只靠本 Workflow Package 驗證。
- 任一未允許 order type 會使正式階段 `fail`。

## 階段 4：Study Events、guarded writer 與 projection

### 正式事件順序

```text
Study Created
→ Preregistration Approved
→ Development Authorized
→ Trials Recorded
→ Trial Registry Frozen
→ Provenance Audited
→ Candidate Frozen
→ Historical Evaluation Completed
→ Nine Challenges Completed
→ Retrospective Replay Completed
→ Independent Review Completed
→ Terminal
```

### 工作

1. 每個 event 獨立保存為 `events/NNNNNN-<type>.yml`。
2. Event envelope 保存 study identity、sequence、previous event digest、event type、時間、actor identity、workflow/policy/source bindings 與 payload digest。
3. 實作 guarded writer commands：
   - create Study、approve preregistration、authorize Development。
   - record Trial、freeze registry、record provenance、freeze candidate。
   - publish evidence、complete stage、review、terminate、recover。
   - rebuild projection、validate Study。
4. 每次寫入前重新驗證完整 chain 和前置條件，成功後才追加 event。
5. `study.yml` 永遠由 events 重建；手動修改不影響權威結果，且 validator 會報 projection mismatch。

### Trial 與 Candidate 規則

- Trial identity 由完整 outcome-relevant exact inputs 決定。
- 相同 inputs 的技術 retry 不新增 trial；任一結果相關 input 改變都新增 trial 並占 budget。
- 已查看結果的失敗、移除與放棄 Trial 永久保留。
- count、唯一 IDs、budget 與 registry digest 由 validator 重算，不能由 caller 宣告。
- Selected Candidate 必須來自完整 Candidate Family。
- Baseline 獨立於 Candidate Family，必須符合 preregistration 中可檢查的 simpler-family 條件。
- Trial budget 用盡仍沒有合格 candidate 時終止為 `fail`。

### 完成條件

- 不合法的跳關和事後修改會被 writer 拒絕。
- 任意移除、插入、換序或修改 event 都會破壞 digest chain。
- 沒有合法 event chain 時，projection 不能提供任何 authority。

## 階段 5：Authority store、lock、journal 與 recovery

### 工作

1. 以設定檔指定 repository 外的 local authority root。
2. 每次發布 event 後，以 atomic create 新增一份 head checkpoint YAML；不得覆寫既有 checkpoint。
3. 每個 Study 使用單一 filesystem lock，避免同時追加。
4. 每次 operation：
   - 在暫存目錄準備 exact canonical bytes 與 digests。
   - 寫入 operation journal。
   - 依序 atomic publish evidence、event、authority checkpoint。
5. Recovery 只能完成相同 journal；目的檔存在但 bytes 不同時停止並回報 integrity error。
6. Validator 比對 event chain、最新 checkpoint 和 journal 狀態。
7. 文件明確聲明：本機 backend 不防止有最高檔案權限的人同時刪除 Study 與 authority records。

### 完成條件

- 在每一個 publication step 模擬中斷後，都能 idempotent recovery 或安全停止。
- 不呼叫 Git，也不依賴 `.git` 存在。
- authority tail 回退、sequence 衝突和不同 bytes retry 都能被發現。

## 階段 6：Role-specific data、folds 與 evidence validation

### Data Snapshots

- Development、quarantine、Historical Evaluation、2025 Replay 使用分開的 snapshots。
- 每份 snapshot 綁定 provider、symbols、timezone、calendar、fields、adjustment policy、ordered Session Inventory 與 digest。
- Development 階段只能取得 Development snapshot。
- Evaluation／Replay snapshots 在 candidate freeze 前不得交給研究者使用。
- Frozen snapshot 可讀但缺 session、重複、額外或重疊時是 `fail`；artifact 無法取得或驗證時是 `indeterminate`。

### Evaluation Folds

- 每個年度重設 positions、cash、cooldown 與 ledger。
- 指標只用該年度最前面的固定 Fold Warmup；warmup 不產生 signal、trade 或 performance。
- 不使用前一年或 2019 quarantine 暖機。
- Strategy 必須固定最大持有期；年末以 entry cutoff 避免建立無法正常完成的交易，不臨時強制平倉。

### Nine Challenges

- 九項各自發布一份 Challenge Evidence。
- 每份綁定相同 candidate、Evaluation snapshot、fold inventories、policy set、qualification spec 和 Source Bundle。
- 隨機進場與漏單 challenge 的 seed 必須 preregistered。
- Challenge IDs 必須完整、唯一且剛好等於正式九項；缺失、重複、binding 不同或 gate failure 都是 `fail`。

### 2025 Replay

- 以 preregistered initial cash 開始，不承接 2024 state。
- 只使用 2025 期間內 Fold Warmup。
- Warmup 不產生 proposal、fill 或 performance。
- 沿用最大持有期與 entry cutoff。
- Broker access 和 real orders 永遠禁止。

## 階段 7：Metrics、Workflow Floors 與 terminal review

### 工作

1. 從 canonical ledger 重算 metrics，不接受 caller-reported metrics 或 passed flag。
2. 使用十進位數字與固定 rounding rule；保存原始 numerator／denominator。
3. 正式 Workflow Floors：
   - Historical completed trades `>= 20`。
   - Traded folds `>= 3`。
   - Positive traded folds／traded folds `>= 60%`。
   - Base compounded return `> 0`、profit factor `> 1.1`。
   - Stress return `> 0`、profit factor `> 1`。
   - Stress drawdown 不超過 preregistered limit。
   - 任一 fold 不超過總交易或總正獲利的 `50%`。
   - Complete-family family-wise confidence `>= 90%`。
   - 2025 Replay 覆蓋完整 sessions、completed simulated fills `>= 12`。
   - Replay base／stress return `> 0`、profit factor `> 1`、drawdown 合規且 critical drift 通過。
4. Study Gates 可以比 floors 嚴格，不能更寬鬆。
5. 交易／fills 不足為 `fail`；缺 artifact、digest mismatch 或無法重算為 `indeterminate`。
6. 拒絕 NaN 與一般 infinity；正毛利且零毛損的 profit factor 可為正無限，但仍必須通過最低交易數。
7. Independent Review 可以由同一人執行，但必須：
   - 只讀 frozen inputs 與 raw evidence。
   - 重新執行 deterministic validator。
   - 不修改既有 evidence。
   - 發布 Terminal Evidence 後才追加 outcome event。

### 完成條件

- `pass` 必須具有所有必要 stage evidence、九項 challenge evidence、Replay evidence 與 Terminal Evidence。
- Terminal Evidence 綁定完整 event-chain head 和所有必要 digests。
- 手動建立一個看似通過的 `study.yml` 不會得到任何 authority。

## 階段 8：範例、反例與 release tests

### End-to-end fixtures

- 完整 `pass` Study。
- 已知 gate failure 的 `fail` Study。
- 缺失／損壞 evidence 的 `indeterminate` Study。
- 可恢復中斷的 `paused` Study。

### 必要反例

- 跳過 stage 或 review 直接填 pass。
- 修改 frozen candidate、threshold、data period 或 evidence。
- Trial 超 budget、重複 ID、count 不一致、隱藏 Trial。
- Candidate 不在 family、Baseline 冒充 candidate 或事後更換。
- Provenance contaminated／unknown 卻繼續。
- 任一 Workflow Floor 邊界值錯誤。
- 九項 challenge 缺失、重複、錯 binding 或錯 seed。
- Fold carry state、使用 quarantine warmup、年末臨時強制平倉。
- Session 缺失、多出、重疊、順序錯誤或 snapshot digest drift。
- 未允許 Proposal Order Type。
- Journal 半完成、不同 bytes retry、authority checkpoint 回退。
- Reviewer 信任 passed flag 或在 review 時修改 frozen evidence。
- Formal run 嘗試網路或 broker access。
- 無 `.git` 環境無法驗證。

### Release gate

```text
uv run pytest
uv run ruff check .
```

另外執行：

- canonical YAML golden verification。
- Source Bundle 與 release-manifest digest verification。
- 無網路／無 broker safety tests。
- 將 Workflow Package 複製到沒有 `.git` 的暫存環境後完成 validate/review。

## 階段 9：文件整理、v011 移除與 release candidate

### 工作

1. 將仍適用的 v011 說明改寫為 v001 自包含指南。
2. 更新 `minimal-executable-study.md`，使術語、階段、folders、events 與 outcomes 和實作一致。
3. 刪除 `strategy-forward-replication-research-v011-guide.md`。
4. 移除所有指向 v011 行為權威、`--v011`、implicit latest 與不存在文件的有效引用；本計畫與 ADR 可保留遷移歷史。
5. 更新 package README，說明：
   - 如何建立與驗證 Study。
   - authority root 如何設定、備份與恢復。
   - Trusted Operator 與本機 authority store 的威脅模型。
   - Independent Review 不要求不同人，但一定要重算。
6. 產生 `release-manifest.yml`，列出 definition、schemas、rules、policies、validators、writers 與 maintained tests 的 exact digests，明確排除 `studies/`。
7. 產生 release test report。
8. 確認沒有 `release.yml`；把 release candidate 交給 trusted approver。

### 完成條件

- Repository 不存在指向 v011 行為權威的有效引用；本計畫與 ADR 的遷移歷史不在此限。
- Workflow Package 不依賴原專案路徑、Git、網路或 broker。
- 所有 tests 與 Ruff 通過。
- `release-manifest.yml` 可重算且沒有包含 `studies/`。
- `release.yml` 不存在。

## 原始缺陷與修復對照

| 原始問題 | 修復方式 | 主要驗收 |
|---|---|---|
| Immutable 欄位讓狀態卡死 | Append-only Study Events＋projection | 完整合法 state path 測試 |
| 可以跳關直接 pass | Guarded writer＋terminal evidence prerequisites | 直接填 pass 反例被拒絕 |
| Trial／candidate 完整性不足 | Registry 重算、budget、membership、digest bindings | 超額、隱藏、錯 membership 測試 |
| Provenance 不影響 outcome | 三態固定 disposition | contaminated／unknown 提前終止 |
| Gate 可過度寬鬆 | Workflow Floors＋Study Gate 不得放寬 | 所有門檻邊界測試 |
| 九項 challenges 沒有逐項證據 | Exact ID set＋每項獨立 artifact | 缺失、重複、錯 binding 測試 |
| Fold 初始狀態不明 | 年度 reset＋in-fold warmup＋entry cutoff | carry／跨年反例被拒絕 |
| 版本權威混亂 | 自包含 v001＋immutable release record | v011 完整移除 |
| Failure policy 漏階段 | 所有正式 gates 共用終止政策 | 每階段 failure path 測試 |
| 規則只是文字 | Schema＋semantic validator＋artifact verifier | 全部反例無法寫入或通過 review |

## 實作順序與依賴

```text
權威規格
  → canonical YAML / schemas
  → local policy releases
  → validator foundations
  → events / writer / projection
  → authority / journal / recovery
  → evidence / metrics / terminal review
  → end-to-end fixtures
  → docs cleanup / release candidate
```

後一階段不得以臨時格式繞過前一階段；例如 writer 開發前，event schema 與 canonical bytes 必須先固定。

## 主要風險

- **Canonical YAML 實作不完整**：以 golden bytes 與拒絕非 canonical input 的測試處理。
- **本機 authority store 被誤認為防惡意攻擊**：文件、CLI warning 與 ADR 明確限制 threat model。
- **外部 artifacts 日後遺失**：Evidence Manifest 必須包含穩定位置、大小與 digest；無法取得時為 `indeterminate`。
- **移植 policy 但缺少相同實作語意**：不沿用舊 release identity，以本地 conformance fixtures 重新發布。
- **Workflow 之間出現重複程式**：這是刻意換取獨立性；只抽取完全無 workflow 語意且已證明穩定的低階工具。
- **同一人兼任 reviewer 被誤解為人員獨立**：文件統一表述為「獨立重算」，不宣稱職責分離。

## Definition of Done

以下全部成立才算完成本計畫：

1. 每項原始缺陷都有對應規則與反例測試。
2. 所有正式 Study mutation 只能經 guarded writer。
3. Validator 能在無 Git、無網路、無 broker 的環境重算四種 Study dispositions。
4. Policy releases、Source Bundle、evidence 與 terminal result 全部由 exact digests 串接。
5. v011 guide 與失效引用已移除，v001 文件和實作一致。
6. `uv run pytest` 與 `uv run ruff check .` 全部通過。
7. Release manifest 與 test report 已產生。
8. `release.yml` 尚未建立，等待 trusted approver 另行核准。
