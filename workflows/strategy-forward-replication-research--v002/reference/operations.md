# v002 日常操作與 runner 契約

## 啟用與角色邊界

本文件的正式操作必須等本版獲准啟用後才能使用。實作者只交付 Release Candidate；不得為了讓指令通過而新增 `release.yml` 或對正式 Study 使用 `--allow-draft`。後者僅供隔離測試。

Study 開發者準備 source、規格與合成案例；核准者提供預先登記與 Development 授權依據。批次工具不替任何人核准。Historical Evaluation 正式執行仍由具權限的角色在候選凍結後處理，其結果只能寫到既定 artifact store。

## 一、prepare

先在 `research/<study-id>/` 準備前版既有規格，以及新的 `runner-contract.yml`。Source Bundle 必須列出兩個正式 runner、其所有研究程式依賴、規格及 implementation contract；runner contract 也必須列入。資料 CSV 不列入這份 preflight source 複本；合成資料完全由 contract 的 rows 產生。

```bash
python workflows/strategy-forward-replication-research--v002/operations/cli.py \
  --repository-root . --authority-root /獨立位置/authority \
  prepare 新研究ID --report /暫存位置/prepare-001.yml
```

此操作依序檢查 ID、規格一致性、內容指紋、策略合成邊界、authority 是否已有此 ID，然後執行完整 runner。失敗不建立正式 Event 或 checkpoint，也不輸出成功報告。報告已存在且內容不同時拒絕覆寫，請另用新檔名。

報告綁定 source、全部主要設定、workflow 工具內容、Python 執行檔及版本、已安裝套件版本、合成資料與證據指紋。建立前再次核對；任何變動必須重跑 prepare。換環境或搬動 repository／authority root 也需要重跑。

`runner-preflight` 可單獨診斷，但其報告不能交給 create。內部 `legacy_checks.py` 是本版固定的舊檢查實作，不是日常入口；原本共用 `research/tools/studyctl.py` 的 v001 命令完全保留。

## 二、runner 使用同一執行路徑

兩種 runner 都接受 `--request <canonical YAML> --output <canonical YAML>`。正式執行與 preflight 共用 `operations.preflight.launch(repository, package, runner, request, output)`；它固定以目前 Python 執行 `-m operations.launch`，工作目錄是提供給 runner 的 repository，Python 模組路徑依序為本版 Package、repository、src。正式操作亦應使用只含 frozen source 與當階段資料的隔離 repository，不將整份市場資料庫放入執行目錄。

request 內有 `stage`、`data_path`、`data_digest`、`preregistration`、`trial_inputs`、`source_bundle`。其他 frozen 設定由 source 中的已綁定路徑載入。runner 必須檢查資料指紋，透過同一個主程式解析參數、呼叫策略、組裝證據並寫出 canonical YAML；不能依「是否合成」改走另一條策略或輸出路徑，也不能以預寫 evidence 代替執行。

Development 輸出為 `candidate` 與 `baseline` 兩個完整 Development evidence。兩者都包含 base／stress 的 raw trades、metrics、diagnostics 與 gates；baseline 不計入候選 family。Historical 輸出沿用 `historical-evaluation.schema.yml`。validator 會從 raw evidence 重算；績效 gate fail 是合法測試結果。

空交易 Development evidence 使用 `validator.artifacts.empty_development_result(preregistration)` 定義的明確表示：交易數為 0、統計不可估計、資格為 fail。這是修正原本直接拋出程式錯誤的情況，不授予候選資格，也不捏造 bootstrap 結果。無交易仍須通過 identity、inputs、seed 等綁定驗證。不得因為尚未產生 evidence 就宣稱沒有接觸真實資料。

runner contract 格式由 `schemas/runner-contract.schema.yml` 定義：

```yaml
protocol: request-output-v1
synthetic_only: true
runners:
  development: research/新研究ID/run_development.py
  historical-evaluation: research/新研究ID/run_historical_evaluation.py
cases:
  # 至少四個案例：每階段各一個 trades 及 no-trades。
  # rows 每列固定為 Date, Open, High, Low, Close, Volume。
  # 必須由策略開發者提供能觸發該策略分支的人工數列，不能複製真實行情。
```

以上僅示意，不是可通過驗證的完整 YAML。每個 case 有 `stage`、`expect`、`rows`，可加 `required_output_keys` 檢查特定診斷輸出分支，例如 `candidate.diagnostics.block_bootstrap`。實際例子與建立程式見 `tests/test_operations.py` 及 `tests/fixtures/runner.py`；這是工具驗收 fixture，不是已驗證的投資策略。新策略若有額外重要分支，開發者需把對應案例納入 contract。

啟動器拒絕 Python 層的網路、外部程序、隔離範圍外讀取及輸出目錄外寫入，保留 Python 環境與系統時區唯讀存取。它延續可信操作人員模型，不是對惡意 Python／原生擴充的作業系統安全沙箱。正式作業仍須使用既定的離線、無券商權限環境。

## 三、create-authorize

準備一份 canonical YAML plan，包含：

- `study_id`、`creator` 與 `identity`；identity 包含 research_round_id、experiment_family、research_owner、historical_evaluation_operator。
- `preregistration`：完整規格，內容必須等於 prepare 綁定的版本。
- `preregistration_actor`、`preregistration_approval`。
- `development_actor`、`development_authorization`。

兩份核准依據各自必須有 `decision: approved`、與對應 actor 相同的 `actor_id`、`role`（trusted-approver 或超級管理者）、`approved_at`、非空 `basis`。scope 分別為 preregistration 與 development-only。這些欄位是可追查的既有核准陳述，工具不產生核准，不以無簽章字串冒充身分驗證。

```bash
python workflows/strategy-forward-replication-research--v002/operations/cli.py \
  --repository-root . --authority-root /獨立位置/authority \
  create-authorize --plan /暫存位置/create-plan.yml --report /暫存位置/prepare-001.yml
```

工具保存不可改寫的原 plan，依序發布 study-created、preregistration-approved、development-authorized。三事件各有自己的 journal 與 checkpoint，**不具有跨事件原子性**。任何一步失敗，都可能已有前面的事件；查看 `studies/<id>/events/` 與 `journals/`，再以相同 plan／report 重試。工具先完成原 prepared journal，再核對既有事件與原計畫，只追加缺少的下一步。不能刪掉 Study 重建、替換 frozen source 或改核准依據後假裝恢復。

底層 writer 的 create 也要求 `--prepare-report`；直接 append study-created 缺少報告會被拒絕。直接追加兩種核准事件仍需要對應核准佐證。既有 recovery 只完成 journal 中相同 bytes。

## 四、freeze-readiness

Development 完成後依既有規則發布 raw evidence、完整 trial registry、provenance 與 selection evidence；不要省略失敗、放棄或移除的 trial。準備真正要送給 candidate-frozen 的 payload：

```bash
python workflows/strategy-forward-replication-research--v002/operations/cli.py \
  --repository-root . --authority-root /獨立位置/authority \
  freeze-readiness 研究ID --actor 操作者 --payload /暫存位置/candidate-freeze.yml
```

這個入口驗證完整事件鏈與 authority，並模擬真正的 candidate-frozen 驗證。它不追加事件，也不把「目前鏈合法」誤當作「已具凍結資格」。正式凍結仍由 guarded writer 發布。

## 失敗與終止

績效 gates、研究目標與 evidence validity（證據是否足以重算）是不同判斷。技術中斷可依 journal／pause 恢復；不可恢復的證據問題沿 evidence-unavailable → study-terminal 結束，不能改寫成乾淨的成功研究。v002 保留前版的 terminal、資料切割、raw evidence 重算與不可覆寫規則。
