# Workflow Packages

本目錄保存各個自包含的 Workflow Package。每個 package 都自行管理研究規則、程式碼、設定、測試、參考文件與 Studies；個別 package 的發布狀態與防竄改 digest，請以該 package 內的 release 文件為準。

## Strategy Forward Replication Research v001

詳細內容請參考 [`strategy-forward-replication-research--v001/README.md`](strategy-forward-replication-research--v001/README.md)。這個 Workflow Package 採用自包含設計，把研究規則、程式碼、設定、測試與實際案例放在同一層目錄中管理：

### 核心設定與發布紀錄

- [`workflow.yml`](strategy-forward-replication-research--v001/workflow.yml)：**研究流程規格總設定**。明確規範研究範圍（美股日線）、資料時間切割（如 2014–2018 開發期、2019 隔離期、2020–2024 歷史評估期），並強制禁止連網下單或在事後偷改參數，避免回測過度擬合（Overfitting，即在歷史數據上看似賺錢、實盤卻失效）。
- [`release.yml`](strategy-forward-replication-research--v001/release.yml)：**正式發布審核紀錄**。記錄經受信任核准者（Trusted Approver）簽核的發布時間與發布版本指紋，只有具備有效簽核的版本才能用於正式策略研究。
- [`release-manifest.yml`](strategy-forward-replication-research--v001/release-manifest.yml)：**檔案防竄改清單**。列出此版本所有核心規則與程式碼的 SHA-256 雜湊值（數位指紋）。若有人擅自修改任何規則或程式碼，寫入工具會因指紋不符而立即拒絕操作。
- [`release-test-report.yml`](strategy-forward-replication-research--v001/release-test-report.yml)：**發布前測試報告**。記錄此版本正式發布前，所有自動化測試全數通過的驗證結果。
- [`IMPLEMENTATION-PLAN.md`](strategy-forward-replication-research--v001/IMPLEMENTATION-PLAN.md)：**實作與驗收歷程**。記錄此研究流程當初從無到有的完整規劃、各階段實作項目與驗收標準。
- [`README.md`](strategy-forward-replication-research--v001/README.md)：**package 起手指南**。說明流程用途、使用方式、備份注意事項與審查原則。

### 工具程式模組

- [`writer/`](strategy-forward-replication-research--v001/writer)：**受保護的寫入工具（Guarded Writer）**。提供命令列介面（CLI），在建立研究、記錄試驗、凍結候選策略等各階段嚴格檢查狀態流轉。寫入時使用兩階段作業日誌（Journals）與本機檢驗節點（Authority Checkpoint），避免因斷電當機留下半完成的損壞檔案，或被偷改退回舊版。
- [`validator/`](strategy-forward-replication-research--v001/validator)：**研究合法性驗證工具**。負責檢查研究的不可竄改事件雜湊鏈（Hash Chain）、YAML 結構規範與指標計算是否正確，提供任何人都能獨立重算的客觀複核工具。

### 規範、結構定義與政策

- [`rules/`](strategy-forward-replication-research--v001/rules)：**研究規則與門檻**。規範研究從建立到終結的狀態機流轉順序、最低樣本數等門檻標準、各階段必要佐證資料，以及故障恢復規則。
- [`schemas/`](strategy-forward-replication-research--v001/schemas)：**資料結構綱要（Schema）**。定義預先登記、歷史評估、資料快照等各事件必須填寫的欄位與格式，確保不會遺漏關鍵研究依據。
- [`policies/`](strategy-forward-replication-research--v001/policies)：**引用的外部環境政策**。包含美股市場交易時段、部位風險管理、標準化下單撮合等獨立政策版本。

### 研究專案與參考資源

- [`studies/`](strategy-forward-replication-research--v001/studies)：**策略研究專案庫**。保存每一個策略研究的完整歷程（如台積電 ADR 或中國 ETF 策略），每個專案內部都各自維護不可竄改的事件鏈與證據檔案。
- [`tests/`](strategy-forward-replication-research--v001/tests)：**自動化測試套件**。包含指標計算、寫入恢復、政策合規與端到端完整流程的測試。
- [`examples/`](strategy-forward-replication-research--v001/examples)：**填寫範例**。提供預先登記（Preregistration）與原始資料包（Source Bundle）的格式範本，供新研究起手參考。
- [`reference/`](strategy-forward-replication-research--v001/reference)：**參考指南與手冊**。包含研究流程的操作規範指引與最小可執行研究的說明文件。
