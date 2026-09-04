# 研究資料與工具

本目錄保存各個 Study（研究個案）在研究過程中使用的規格、資料來源描述、執行程式與
evidence（佐證資料）。它比較像「研究執行工作區」：方便重現某個 Study 使用了什麼規則、
資料與程式。

研究流程的規則、資料格式、validator（驗證工具）、writer（受保護的寫入工具），以及
Study 的不可改寫事件鏈，請以 [`workflows/README.md`](../workflows/README.md) 和
[`strategy-forward-replication-research--v001`](../workflows/strategy-forward-replication-research--v001/)
為準。正式狀態請看該 Workflow Package 底下的
`studies/<study-id>/study.yml` 與 `events/`；不要只依 `research/` 中某個檔案是否存在，
或某份 YAML 的 `outcome` 欄位，手動推導或修改 Study 狀態。

## 目錄總覽

```text
research/
├── README.md                         # 本目錄導覽
├── market-data/                      # 多個 Study 可共用的不可覆寫市場資料
│   ├── README.md
│   └── yahoo/                        # Yahoo Finance 快照與品質報告
├── tools/                            # 下載資料與執行 Study 前置檢查的工具
├── <study-id>/                        # 單一 Study 的規格、程式、資料與 evidence
│   ├── *.yml                         # 研究規格、資料清冊、證據與事件 payload
│   ├── run_*.py                      # 依 frozen inputs 產生 evidence 的 runner
│   ├── event-payloads/                # 部分 Study 使用的事件 payload 子目錄
│   └── data/snapshots/               # 部分舊 Study 保存的本地資料快照
└── __init__.py                       # 讓 research 可作為 Python package 匯入
```

`__pycache__/` 是 Python 自動產生的暫存編譯檔，不是研究輸入或結果，也不應拿來判斷
Study 是否已執行。

## Study 研究個案

目前共有 13 個 Study 目錄：5 個 FXI 個案與 8 個 TSM 個案。下表的狀態是目前
Workflow Package 的 `study.yml` 投影所顯示的狀態；若日後研究繼續推進，請重新查看該
投影與事件鏈。

### FXI 深度回檔系列

這組個案都研究 FXI 的深度回檔、超賣與波動條件；版本差異主要在 ClosePos、退場後
cooldown（冷卻期）與每筆交易風險預算。

| Study | 研究方向 | 目前流程狀態 |
| --- | --- | --- |
| [`fxi-deep-pullback-no-closepos-cd7-v001`](fxi-deep-pullback-no-closepos-cd7-v001/) | 移除 ClosePos 條件，訊號後採 7-session cooldown；這是目前有完整 Development 與 2020--2024 Historical Evaluation 結果的 FXI 個案。 | `terminal / fail`；[Study 狀態](../workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-no-closepos-cd7-v001/study.yml) |
| [`fxi-deep-pullback-no-closepos-exitcd7-v001`](fxi-deep-pullback-no-closepos-exitcd7-v001/) | 把 7-session cooldown 的計時起點明確固定在部位完成退場後，研究無 ClosePos 的退場冷卻版本。 | `candidate-frozen / pending`；[Study 狀態](../workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-no-closepos-exitcd7-v001/study.yml) |
| [`fxi-deep-pullback-risk2-exitcd7-v001`](fxi-deep-pullback-risk2-exitcd7-v001/) | 在無 ClosePos、退場後 7-session cooldown 的規則上，加入每筆交易約 2% 的固定 stop 風險預算。 | `candidate-frozen / pending`；[Study 狀態](../workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-risk2-exitcd7-v001/study.yml) |
| [`fxi-deep-pullback-risk2-exitcd7-devverify-v001`](fxi-deep-pullback-risk2-exitcd7-devverify-v001/) | 對 risk2 版本做 Development evidence 的重算與流程驗證，重點是確認規格、程式與指標沒有不同步，不是另一次自由調參。 | `candidate-frozen / pending`；[Study 狀態](../workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-risk2-exitcd7-devverify-v001/study.yml) |
| [`fxi-deep-pullback-risk2-exitcd7-seedfix-v001`](fxi-deep-pullback-risk2-exitcd7-seedfix-v001/) | 對 risk2 版本重新固定 Development bootstrap 使用的預先登記 seed，驗證修正後的程序仍符合原有 gates。 | `candidate-frozen / pending`；[Study 狀態](../workflows/strategy-forward-replication-research--v001/studies/fxi-deep-pullback-risk2-exitcd7-seedfix-v001/study.yml) |

第一個 FXI Study 另有一份人類可讀的結果說明，可從
[`fxi-deep-pullback-no-closepos-cd7-v001/README.md`](fxi-deep-pullback-no-closepos-cd7-v001/README.md)
開始閱讀。

### TSM 均值回歸系列

這組個案研究 TSM 的均值回歸條件，以及「異常成交量先出現，再用價格或 RSI 確認」是否
能改善 setup（可交易訊號組合）的穩健性。

| Study | 研究方向 | 目前流程狀態 |
| --- | --- | --- |
| [`tsm-mean-reversion-volume-leads--v001`](tsm-mean-reversion-volume-leads--v001/) | 初版「量先於價」條件：異常成交量必須出現在訊號日前 5 個 XNYS session 內。 | `terminal / indeterminate`；Development source/data 驗證不一致，無法形成可判定的 outcome；[Study 狀態](../workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-leads--v001/study.yml) |
| [`tsm-mean-reversion-volume-leads--v002`](tsm-mean-reversion-volume-leads--v002/) | 沿用初版量先條件的修正版 Development 研究。 | `terminal / fail`；[Study 狀態](../workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-leads--v002/study.yml) |
| [`tsm-mean-reversion-volume-leads--v003`](tsm-mean-reversion-volume-leads--v003/) | 在量先條件外，要求訊號日收盤低於前一個 session，測試帶有下跌方向確認的 setup。 | `terminal / fail`；[Study 狀態](../workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-leads--v003/study.yml) |
| [`tsm-mean-reversion-volume-lead-setup--v003`](tsm-mean-reversion-volume-lead-setup--v003/) | 不要求訊號日收盤方向，只保留量先於價的 setup，測試是否能增加可交易樣本。 | `terminal / fail`；[Study 狀態](../workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-volume-lead-setup--v003/study.yml) |
| [`tsm-mean-reversion-reversal-trigger--v001`](tsm-mean-reversion-reversal-trigger--v001/) | 在量先條件外，要求訊號日收盤高於前一個 session，測試反轉觸發確認。 | `terminal / fail`；[Study 狀態](../workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-reversal-trigger--v001/study.yml) |
| [`tsm-mean-reversion-reversal-trigger--v002`](tsm-mean-reversion-reversal-trigger--v002/) | 反轉觸發條件的另一個獨立版本；Study、candidate 與 source bundle 都各自綁定。 | `terminal / fail`；[Study 狀態](../workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-reversal-trigger--v002/study.yml) |
| [`tsm-mean-reversion-two-stage-volume-reversal--v001`](tsm-mean-reversion-two-stage-volume-reversal--v001/) | 兩階段確認：先觀察異常成交量，再用反彈價格與 RSI(2) 條件確認止跌，避免在暴跌途中接刀。 | `candidate-frozen / pending`；[Study 狀態](../workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v001/study.yml) |
| [`tsm-mean-reversion-two-stage-volume-reversal--v002`](tsm-mean-reversion-two-stage-volume-reversal--v002/) | 兩階段成交量反轉條件的另一個獨立版本，保留自己的規格、程式 digest 與 evidence。 | `candidate-frozen / pending`；[Study 狀態](../workflows/strategy-forward-replication-research--v001/studies/tsm-mean-reversion-two-stage-volume-reversal--v002/study.yml) |

## 共用市場資料

[`market-data/`](market-data/) 保存可被多個 Study 參考的 immutable（不可覆寫）市場資料。
目前有 Yahoo Finance 的 TSM `auto_adjust` 日線快照與同名品質報告；檔名包含內容的
SHA-256 digest（數位指紋），所以不應另建會隨時間變化的 `latest.csv`。

- [`market-data/README.md`](market-data/README.md)：說明資料快照、XNYS 交易日清冊、品質檢查與 Study 如何引用資料。
- `market-data/yahoo/*.csv`：固定欄位的 `Open`、`High`、`Low`、`Close`、`Volume` 日線資料。
- `market-data/yahoo/*.quality.yml`：記錄交易日是否缺漏、重複、排序錯誤，以及 OHLCV 是否有不合理值。

部分較早的 Study 仍在自己的 `data/snapshots/` 保存 Study-local 快照；這是相容性做法，
新的 Study 應優先引用這裡的共用快照，並在自己的資料 manifest 記錄完整檔名與 digest。

每個正式 Study 的五種資料角色用途如下：

| 角色 | 實際用途 |
| --- | --- |
| `warmup-only` | 只用來累積均線、RSI 等指標的歷史觀察值，不產生訊號或交易。 |
| `development` | 用來產生 Development trial 與檢查預先登記的最低 gates。 |
| `quarantine` | 隔離期資料；保留結構與 session 檢查，但不讓研究者把它當成開發或正式結果使用。 |
| `historical-evaluation` | 預先固定的 2020--2024 正式歷史評估資料。 |
| `retrospective-execution-replay` | 預先固定的 2025 歷史成交重播資料；只有前段必要 gate 通過時才可執行。 |

## Study 內部檔案

不是每個 Study 都已走到相同階段，因此下列檔案有些只會在特定版本出現。檔案的存在與否
反映該份工作區保存了哪些產物，不代表可以跳過 Workflow 的事件鏈檢查。

### 研究規格與身份

- [`preregistration.yml`](tsm-mean-reversion-volume-leads--v003/preregistration.yml)：**預先登記**。固定假說、候選家族、baseline、訊號與成交規則、成本、日期切割、gates、robustness challenges 與亂數 seed。看過正式結果後修改它，會改變研究身份，不能當成同一 Study 的小修正。
- [`candidate-definition.yml`](tsm-mean-reversion-volume-leads--v003/candidate-definition.yml)：**候選策略的精確定義**。把訊號條件、資料調整方式、停損／停利、持有期間、部位大小與 base／stress 成本寫成可執行的固定值。
- [`qualification-spec.yml`](tsm-mean-reversion-volume-leads--v003/qualification-spec.yml)：**數值門檻**。定義交易筆數、報酬、profit factor、最大回撤、年度分布等指標要如何比較；它只說明「怎樣算通過」，不是結果本身。
- [`implementation-contract.yml`](tsm-mean-reversion-volume-leads--v003/implementation-contract.yml)：**實作契約**。明確固定策略引擎位置、指標公式、有效歷史長度、not-ready 行為與特殊 RSI 邊界值，避免同一個欄位名稱在不同程式中代表不同意思。部分較早 Study 沒有獨立檔案，內容可能在 candidate 或其他 frozen manifest 中。
- [`source-bundle.yml`](tsm-mean-reversion-volume-leads--v003/source-bundle.yml)：**程式來源清冊**。列出會影響結果的程式、測試、設定與依賴檔案及其 digest；它讓重跑時能確認使用的是同一份程式，而不是工作區裡碰巧存在的最新版。
- [`development-trial-inputs.yml`](tsm-mean-reversion-volume-leads--v003/development-trial-inputs.yml)：**一次 Development trial 的固定輸入**。綁定 candidate、資料、成本、source bundle 與執行所需的身份資訊。

### 資料來源與快照

- `data-snapshot-acquisition.yml`：**原始資料取得與血緣清冊**。記錄 provider、ticker、日期範圍、原始檔案路徑與 digest、品質報告，以及由完整資料切出的角色視圖。
- `data/snapshot-acquisition.yml`：部分較早 Study 使用的相同用途路徑；閱讀時要以該 Study 自己的 `source-bundle.yml` 和 digest 為準。
- `data-snapshot-set.yml`：**五種資料角色的完整清單**。除了日期，也固定每個角色實際包含的 session inventory 與 `data_digest`，用來防止把開發資料誤當成 Evaluation 資料。
- `data/snapshots/`：**Study-local CSV 快照**。檔名通常直接包含 SHA-256；檔案不可任意替換或重新下載，否則 manifest 中的 digest 綁定會失效。

### 執行程式

- [`run_development.py`](tsm-mean-reversion-volume-leads--v003/run_development.py)：**Development runner**。只讀取指定的 warmup 與 development 快照及 frozen inputs，產生 Development evidence；正式執行應保持離線。
- [`run_historical_evaluation.py`](tsm-mean-reversion-volume-leads--v003/run_historical_evaluation.py)：**Historical Evaluation runner**。使用已凍結的 evaluation 快照與規格產生正式評估 evidence；runner 本身不等於發布 Study Event。
- [`acquire_snapshots.py`](tsm-mean-reversion-volume-leads--v003/acquire_snapshots.py)：部分較早 TSM Study 使用的資料取得／切分腳本。新的共用下載入口是 [`tools/download_market_data.py`](tools/download_market_data.py)。

### Evidence 與流程 payload

- `development.yml` 或 `development-evidence.yml`：**Development 結果**。保存實際交易、base／stress 指標、bootstrap 或 leave-one-year-out 診斷、每個 gate 的實際值與所有輸入 digest；Development 通過不代表正式 Evaluation 一定通過。
- `selection-evidence.yml`：**候選選擇證據**。保存完整 candidate family、排序規則與唯一入選 candidate 的可重算依據。
- `historical-evaluation.yml`：**Historical Evaluation 的原始結果**，通常包含交易與分段資料。
- `historical-evaluation-report.yml`：**Historical Evaluation 的詳細重算報告**，包含結果指標、失敗 gates、輸入綁定與必要的交易明細。
- `terminal-evidence.yml`：**Study 終止證據**。由完整 frozen inputs 與必要 evidence 重算最終 `fail` 或 `indeterminate`，並說明為何停止；它不是可以手填的狀態欄位。
- `provenance.yml`：**來源可信狀態證據**。記錄在正式結果揭露前是否受到後段結果影響，以及資料取得時執行了哪些隔離控制。
- `development-authorization.yml`：**Development 執行授權範圍**，例如只能使用 warmup 與 development role、不得連網。
- `*-approved.payload.yml`、`*-authorized.payload.yml`、`trial-recorded.payload.yml`、`trial-registry-frozen.payload.yml`、`candidate-frozen.payload.yml`、`historical-evaluation-completed.payload.yml` 與 `study-terminal.payload.yml`：**待發布的事件 payload**。它們保存一次流程操作要發布的欄位與 evidence digest；正式事件鏈仍在 Workflow Package 的 `events/`，不應直接改這些 payload 來改變狀態。
- `event-payloads/`：部分較新的 Study 把上述 payload 集中放在這個子目錄；這只是檔案布局差異，不代表它有另一套流程規則。
- `README.md`：若該 Study 有提供，這是給人閱讀的研究摘要；它不能取代 manifest、evidence 或 Workflow 的正式事件鏈。

## 研究工具

### 市場資料下載與檢查

[`download_market_data.py`](tools/download_market_data.py) 下載單一 ticker 的 Yahoo Finance
`auto_adjust`、1d OHLCV 資料，預設使用 XNYS 交易日曆。保存前會檢查交易日清單、欄位、
缺值、非有限值、價格正值、成交量，以及 `Low <= Open/Close <= High` 等關係，並產生
同名 `.quality.yml`。輸出檔名含內容 digest，因此不會被新的下載覆寫。

### Study 前置檢查

[`studyctl.py`](tools/studyctl.py) 是唯讀的 Study preflight（前置檢查），不是 writer。
它可以在建立或 candidate freeze 前檢查：

- `identity`：Study、candidate family 與 trial identity 是否一致，是否誤引用其他 Study 的檔案。
- `contract`：實作契約、指標就緒邊界、策略引擎與 Source Bundle 是否對得上。
- `synthetic`：用不含正式市場資料的合成邊界案例檢查 RSI、指標 ready、holding 與 cooldown 行為。
- `freeze`：檢查是否具備進入 candidate freeze 的必要規格與 evidence。

從 repository 根目錄執行：

```bash
uv run python research/tools/studyctl.py --repository-root . all <study-id>
```

[`studyctl-contract.example.yml`](tools/studyctl-contract.example.yml) 是 implementation
contract 的最小填寫範例。正式寫入事件仍必須使用 Workflow Package 的 validator 與 guarded
writer；preflight 通過不會自行發布事件。

## 閱讀與操作順序

要理解一個 Study 時，建議依序查看：

1. 先看 [`workflows/README.md`](../workflows/README.md)，了解研究流程與不可降低的底線。
2. 在 `research/<study-id>/preregistration.yml` 看假說、資料切割、執行語意與事前 gates。
3. 依序核對 `candidate-definition.yml`、`implementation-contract.yml`、`source-bundle.yml` 與 `data-snapshot-*`，確認策略、程式與資料是同一組 frozen inputs。
4. 需要重現 Development 或 Evaluation 時，再看對應的 `run_*.py` 與 `development*.yml`／`historical-evaluation*.yml`。
5. 要確認研究走到哪裡或為何終止，最後查看 `workflows/.../studies/<study-id>/study.yml` 與 `events/`，不要手動編輯任何 outcome 或事件檔案。

這份 README 只新增導覽與用途說明，沒有搬移、重新命名或修改任何既有 Study、資料快照
或 digest 綁定。
