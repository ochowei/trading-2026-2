# trading-2026-2

Python 3.11 project managed with uv.

## 目前研究

- [`fxi-deep-pullback-no-closepos-cd7-v001`](research/fxi-deep-pullback-no-closepos-cd7-v001/README.md)：FXI 深度回檔、超賣、短期波動擴張與七-session cooldown 的可否證研究。2020--2024 Historical Evaluation 未通過，Study 已正式終止為 `fail`，假說遭否證。

## 核心流程控制與資料工具（CLI）

在進行量化交易策略研究時，為避免「回測過度擬合（Overfitting，即在過去歷史數據上表現完美但實盤失效）」、「看過回測結果後事後偷改參數」或「寫入檔案意外中斷導致資料損毀」，本專案提供三支核心 CLI（命令列工具），以固定的狀態流轉與資料檢驗協助研究保持客觀、可重現。

### 1. Study 唯讀前置檢查工具 (`research/tools/studyctl.py`)

* **實際問題與影響**：
  在建立新研究（Study）或將策略參數正式鎖定（Candidate Freeze，凍結候選策略）前，如果研究規格、檔案路徑、或指標計算規則（例如移動平均線或相對強弱指標 RSI 初始期未累積足夠數據時的處理方式）有任何疏漏與不同步，後續耗時的回測可能完全白費，甚至得出錯誤的策略結論。此工具是**唯讀前置檢查工具（Preflight）**，只讀取檔案並回報問題，不會建立 Study Event。
* **基本執行語法**：
  ```bash
  uv run python research/tools/studyctl.py [全域參數] <子命令> <study-id>
  ```
* **全域參數**：
  * `--repository-root <path>`：指定專案根目錄（預設是此工具所在的專案根目錄）。從其他目錄執行時，使用它可避免讀到錯的 `research/` 或 `workflows/`。
  * `--authority-root <path>`：指定本機 authority checkpoint（權威檢查點）目錄。`freeze` 或 `all` 會用它比對 Event（研究事件）數量與 digest（內容指紋），偵測事件遺失、回退或內容不一致；它不是作業系統層級的檔案防護。
* **子命令（Subcommands）**：
  * `precreate <study-id>`：在第一個 `study-created` Event 前，檢查同名 `research/<study-id>/` 裡的 `preregistration.yml`、`candidate-definition.yml`、`qualification-spec.yml`、`development-trial-inputs.yml`、`source-bundle.yml` 與 implementation contract（實作契約）是否能讀取，並核對跨檔案 digest 與身份綁定。它不需要已存在 Study Event。
  * `identity <study-id>`：檢查研究標識（Study ID）、研究目錄（`research/<study-id>`）與設定檔中的路徑宣告是否一致，避免複製貼上舊研究範本時殘留舊版本路徑。
  * `contract <study-id>`：核對指標實作契約（Implementation Contract），檢查移動平均線（SMA）、RSI 等指標所需的歷史暖機交易天數，以及指標未就緒時的值，避免策略偷用尚未填滿的數值。
  * `synthetic <study-id>`：使用不含正式市場資料的合成測試案例，檢查 RSI、指標 ready 邊界、價格跳空、同一交易日同時觸發停損與停利、持有期及 cooldown 行為。
  * `freeze <study-id>`：在策略凍結（Candidate Freeze）前，檢查事件鏈、Source Bundle、必要佐證文件與 validator 是否允許進入下一階段；已合法 terminal 且沒有 candidate 的 Study 會標示為不適用。
  * `all <study-id>`：依序執行 `identity`、`contract`、`synthetic`、`freeze`；**不包含** `precreate`。`precreate` 必須在建立 `study-created` Event 前另外執行，不能用 `all` 取代。

`studyctl` 的輸出固定是 JSON。檢查通過時 exit code 為 `0`，找到檢查問題時為 `1`，命令或環境無法執行時為 `2`。正式 candidate freeze 應提供 `--authority-root`，並檢查所有 warning，而不能只看 exit code。
* **實作契約範例（`research/<study-id>/implementation-contract.yml`）**：
  以下只是欄位範例；實際的 engine path（策略引擎路徑）、規格常數與指標欄位，必須和該 Study 的程式及 Source Bundle 完全一致。
  ```yaml
  schema_version: 1
  engine:
    path: src/trading_2026_2/example_strategy.py
    spec_constant: DEFAULT_SPEC
    cost_constant: BASE_COST
  indicator_contract:
    required_history_sessions: 25
    columns:
      sma: sma_20
      rsi: rsi_2
      volume_lead: prior_volume_spike_ratio
    sma:
      lookback: 20
      min_periods: 20
      not_ready: null
    rsi:
      length: 2
      formula: simple-rolling-mean
      min_periods: 2
      not_ready: null
      zero_gain_and_loss: 50
      zero_loss_only: 100
      zero_gain_only: 0
    volume_lead:
      volume_average_length: 20
      average_min_periods: 20
      prior_session_window: 5
      lead_min_periods: 5
      uses_prior_sessions_only: true
  ```

---

### 2. 受保護的狀態寫入工具 (`workflows/strategy-forward-replication-research--v001/writer/cli.py`)

* **實際問題與影響**：
  研究流程禁止手動修改已發布的檔案或任意竄改回測狀態。如果寫入過程中遇到斷電、系統當機，仍可能只完成部分檔案；因此工具用兩階段作業日誌（Journal）固定待發布的確切內容，讓 `recover` 能用同一批 bytes（檔案內容）完成中斷操作。個別檔案採原子寫入（Atomic，即單一檔案不會留下半截內容），但「發布佐證檔案、追加 Event（研究事件）、更新 projection（由事件重建的狀態摘要）」是分開的步驟，不代表整個多指令流程要嘛全部成功、要嘛完全不變。
* **基本執行語法**：
  ```bash
  uv run python workflows/strategy-forward-replication-research--v001/writer/cli.py --authority-root <路徑> <子命令> [參數]
  ```
* **全域參數**：
  * `--authority-root <path>`（必要）：指定獨立於研究目錄外的本機 authority checkpoint 目錄，保存每次 Event 的 SHA-256 內容指紋。後續 `validate` 會用它偵測 Event 與 checkpoint 數量或內容不一致；它不是簽章，也不能阻止擁有檔案權限的人直接修改檔案。
  * `--workflow-root <path>`：指定流程套件根目錄（預設是此 CLI 所屬的套件路徑）。路徑錯誤會讓 writer 讀到錯的規則或 release。
  * `--allow-draft`：允許在尚未正式發布核准的草稿版本上進行開發與測試；正式研究不得使用，否則不會受到正式 release 檢查的保護。
* **子命令與專屬參數**：
  * `create`：正式建立全新研究個案（Study）。
    * `--study-id`：研究唯一名稱（例如 `tsm-mean-reversion-v001`），決定 Event 與 artifact 寫入哪個 Study；填錯會把操作指向錯的研究。
    * `--actor`：執行操作者名稱，會寫入 Event 供日後追查誰執行了這一步。
    * `--research-round`：所屬研究輪次標識，用來把這個 Study 和研究批次綁在一起；填錯會造成身份或稽核資料不一致。
    * `--experiment-family`：實驗家族名稱，說明候選策略屬於哪一組可比較的研究；錯誤的家族名稱會讓後續選擇與稽核難以對應。
    * `--research-owner`：研究負責人名稱，保存責任歸屬，方便交接與追查。
    * `--replay-operator`：歷史重播／回測執行人員名稱，保存實際執行者，不等同於策略結果本身。
    * `--source-bundle`：canonical YAML（欄位順序與表示方式固定的 YAML）來源清冊，列出程式碼與設定檔及其 SHA-256 digest；內容或 digest 不一致時，後續 writer／validator 會拒絕使用這份 Study。
  * `append`：追加研究事件（Study Event，如開發完成、候選凍結、歷史評估完成等）；事件只允許依序新增，內容異常會由 hash chain（雜湊鏈）偵測。
    * `--study-id`：要追加事件的 Study；錯誤的 ID 會把事件寫到錯的研究或找不到目標。
    * `--actor`：追加這筆事件的操作者，會成為事件鏈的一部分。
    * `--event-type`：事件類型名稱，會推進 workflow state machine（狀態機）；順序或類型不符合規則時，事件不會被追加。
    * `--payload`：事件資料檔案路徑；內容必須是 canonical YAML（欄位順序與表示方式固定的 YAML），且必須符合該事件的 schema，否則寫入會失敗。
  * `publish-artifact`：發布研究佐證檔案（Artifact，如回測原始數據），並計算其 SHA-256 數位指紋。
    * `--study-id`：目標研究名稱，決定 artifact 寫入哪個 Study。
    * `--path`：Study 目錄內的目標相對路徑；不能穿越到 Study 外，已存在且內容不同的檔案不會被覆寫。
    * `--source`：來源檔案路徑；CLI 會以 canonical YAML 讀取它並重新保存，因此不能直接傳 CSV 或其他任意二進位檔。
  * `validate`：校驗指定研究的事件鏈、引用 artifact 與 authority checkpoint；發現不一致時只回報錯誤，不會替你修正檔案。
    * `--study-id`：要驗證的 Study 名稱。
  * `recover`：當寫入操作遭遇中斷（例如當機）時，從 prepared journal 恢復同一筆操作；它只能使用 journal 內已固定的 bytes，不允許換資料後重試。
    * `--study-id`：要恢復的 Study 名稱；恢復完成後應再次執行 `validate`，再繼續下一個操作。

---

### 3. 市場行情下載與品質檢驗工具 (`research/tools/download_market_data.py`)

* **實際問題與影響**：
  量化回測若使用會隨時間變動或品質有缺陷的資料，將無法精確重現研究成果。這支工具從 Yahoo Finance 下載指定 ticker 的日線行情，並對照交易所日曆（預設為 XNYS）檢查交易日是否缺漏，再檢查每根 K 線的 OHLCV（開盤價、最高價、最低價、收盤價與成交量）是否有缺值（NaN）、非正價格、負成交量或上下界矛盾。它不檢查跨日價格跳空；跳空與同日停損／停利順序是策略引擎的 synthetic 測試範圍。產出的 CSV（逗號分隔值）檔名包含 SHA-256 內容指紋，且同名品質報告會記錄該指紋；工具不會覆寫不同內容的既有檔案，但這不等於檔案系統層級的不可竄改。
* **基本執行語法**：
  ```bash
  uv run python research/tools/download_market_data.py --ticker <代碼> --start <起始日> --end <結束日> [選項]
  ```
* **參數說明**：
  * `--ticker <代碼>`（必要）：Yahoo Finance ticker（例如 `TSM`、`FXI`）；使用預設 XNYS 日曆時，應提供在該交易所交易的標的。
  * `--start <YYYY-MM-DD>`（必要）：資料起始日期（含當日）。
  * `--end <YYYY-MM-DD>`（必要）：資料結束日期（含當日，程式內部會自動轉換為 Yahoo API 所需的排除性結束日）。
  * `--output-dir <path>`：快照檔案輸出目錄（預設為 `research/market-data/yahoo`）。
  * `--calendar <名稱>`：交易所交易日曆名稱（預設為美股 `XNYS`），用以檢查交易時段清冊（Session Inventory）是否有休市日誤載或交易日缺漏。
  * `--ohlc-tolerance <數值>`：開高低收價格邊界關係允許的浮點數微小誤差上限（預設為 `1e-10`）。

---

## 流程規範檢核與自動化輔助工具（Workflow & Agent Scripts）

這些腳本位於 `.agents/skills/` 目錄下，主要供自動化 Agent 或研究者在執行特定的研究生命週期階段時確認範圍與前置條件。它們會回報檢查結果，但不會取代 workflow validator（流程驗證器），也不會自動發布 Event。

### 1. 盲檢討範圍審核腳本 (`.agents/skills/blind-review-strategy-study/scripts/check_scope.py`)
* **實際問題與影響**：
  在進行「盲檢討（Blind Review，即在不查看正式評估結果的前提下檢視研究假設與程式碼）」時，如果檢討了錯誤的 workflow 或不合規的目錄，檢討可能失去效力；因此要先把檔案範圍固定下來。
* **用途與功能**：確認指定目標是 `strategy-forward-replication-research--v001` 底下的直接 Study 目錄，且具備檢討需要的 `preregistration.yml`、`candidate-definition.yml`、`development.yml`。這支腳本只做路徑與必要檔案檢查，不負責判定 Study 沒有 Evaluation 結果。
* **執行範例**：
  ```bash
  uv run python .agents/skills/blind-review-strategy-study/scripts/check_scope.py <study-id或目錄路徑>
  ```

### 2. 新研究建立前規格檢驗腳本 (`.agents/skills/build-strategy-study-to-freeze/scripts/check_new_study.py`)
* **實際問題與影響**：
  若研究命名重複、格式不符或在錯誤的流程環境下建立，可能導致舊有研究資料被意外覆寫，破壞研究不可竄改的承諾。
* **用途與功能**：檢查欲建立的 Study ID 格式是否安全合規（3–63 個小寫英數字與連字號）、確認 `release.yml` 檔案存在，並確認同名 Study 與 research 目錄不存在，避免重複覆寫或冒充新研究。它不會驗證 release manifest、測試報告或 digest；那些檢查由正式 writer／validator 負責。
* **執行範例**：
  ```bash
  uv run python .agents/skills/build-strategy-study-to-freeze/scripts/check_new_study.py <study-id> [--repository-root <path>]
  ```

### 3. 候選策略凍結狀態驗證腳本 (`.agents/skills/run-strategy-historical-evaluation/scripts/check_candidate_frozen.py`)
* **實際問題與影響**：
  歷史評估（Historical Evaluation）階段是不可逆的盲測驗證。若研究者在策略尚未正式凍結時就偷跑評估，或者在評估後又回頭微調參數，研究結論將徹底失效（即資料窺探偏差 Data Snooping Bias）。
* **用途與功能**：嚴格檢查 Study 的 `events/` 是否恰好有 7 個檔案，最後一個是 `000007-candidate-frozen.yml`，並核對 Source Bundle 列出的檔案 digest。若 Source Bundle 沒有 `run_historical_evaluation.py`，腳本仍可能回傳 `eligible`，但會標示 `runner_status: "adapter-required"`；這表示需要先建立並測試 adapter（轉接程式），不代表已有 frozen runner（已凍結的評估執行程式）。腳本也只檢查事件階段，不會掃描所有目錄來保證沒有 Evaluation artifact。
* **執行範例**：
  ```bash
  uv run python .agents/skills/run-strategy-historical-evaluation/scripts/check_candidate_frozen.py <study-id或目錄路徑> [--repository-root <path>]
  ```

### 4. 歷史評估數據獨立重算工具 (`.agents/skills/run-strategy-historical-evaluation/scripts/recompute_historical_evaluation.py`)
* **實際問題與影響**：
  傳統研究常由操作者自行填寫勝率或年化報酬等指標，容易引發作假或計算口徑不一的誠信問題。
* **用途與功能**：基於 Workflow Validator（流程驗證器：依固定規則重新檢查資料與門檻），從指定的 canonical raw evidence（固定格式的原始評估資料）重新計算整體績效與由各 Fold（年度評估分段）組成的分布指標，再比對研究門檻（Gate）。它不採信人工或呼叫方預先填寫的 `passed` 標記；但它只重算你傳入的 evidence，完整的 Study、candidate、資料與 artifact identity（身份）綁定仍要由其他 preflight／validator 步驟完成。
* **執行範例**：
  ```bash
  # 僅檢查評估門檻是否皆受 validator 支援
  uv run python .agents/skills/run-strategy-historical-evaluation/scripts/recompute_historical_evaluation.py <study-id> --check-gates-only

  # 從原始佐證重新計算指標並判定是否通過
  uv run python .agents/skills/run-strategy-historical-evaluation/scripts/recompute_historical_evaluation.py <study-id> <evidence-path>
  ```
