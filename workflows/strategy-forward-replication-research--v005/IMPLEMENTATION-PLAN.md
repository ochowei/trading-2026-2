# v005 Draft 與 Release Candidate 驗證計畫

v005 是 v004 的後繼版本，保留 v004 的研究門檻、Policy 引用、Study 引用與明確派工。新增可變數量的資產資料，讓 TSM 與 SOXX 或更多參考資產在同一次試驗中逐檔驗證。v004 的已發布 Package、Release Record、Study 與 evidence 保持原樣。

## Draft 交付

| 範圍 | 對應內容 |
| --- | --- |
| 多資產計畫 | `schemas/development-plan.schema.yml`、`schemas/evaluation-plan.schema.yml` 接受 1–16 筆有穩定 ID、用途、來源、日期及獨立 digest 的清單。 |
| 資料檢查與隔離 | `operations/multi_asset.py` 驗證 XNYS 日期、六欄 CSV、完整交易日、跨資產對齊、大小與受限路徑；`lifecycle.py`、`evaluation.py` 只複製核對過的資料進隔離 workspace。 |
| runner 與來源綁定 | `preflight.py`、`runtime_manifest.py`、`publication.py`、`validator/artifacts.py` 綁定逐資產清單、合成案例、runner request、manifest 與 candidate／baseline evidence。 |
| 凍結與評估 | `data-snapshot.schema.yml` 與 `validator/artifacts.py` 讓每個資料角色分別記錄資產 digest；`validator/evaluation.py` 檢查 Evaluation request 與凍結總 digest。 |
| 既有單資產路徑 | 保留原 `data_path`／`data_digest` 介面，避免新版本內沿用單資產的研究路徑失效。 |

## TASK-026 執行者的 Release Candidate 檢查

1. 核對 Package 自包含，沒有正式 `release.yml`、正式 manifest／test report 或既有 Study；逐檔檢查 v004 的已發布內容未被修改。
2. 執行所有 canonical YAML 與 schema 驗證，檢查 workflow、release、Policy、runner、snapshot、Development／Evaluation plan、runtime manifest 與 publication schema 的一致性。
3. 執行 validator、guarded writer、state transitions、artifact digest、failure／recovery、policy conformance 反例；確認多資產每份資料、request、runtime manifest、snapshot 與事件證據可重建。
4. 使用純合成 fixture 跑 1、2、3 個以上資產的 Development 與 Historical Evaluation 端到端案例，含 terminal dispositions；確認單資產舊路徑仍通過。明確覆蓋重複 ID、缺檔、digest 漂移、日期錯位、缺漏、混入受限資料、超額與隔離越界拒絕。
5. 執行必要的全套 pytest、Ruff、Release Candidate checker；根據實際結果產生 `release-manifest.yml` 與 `release-test-report.yml`。不可用測試摘要代替可重算的檔案與 digest。
6. 由獨立 Trusted Approver 檢視並建立 `release.yml`；核准未取得時維持 Release Candidate，不得宣稱 Active。其後才依 Lifecycle 更新治理狀態並交接 TASK-023。

`tests/test_release_candidate.py` 同時以隔離副本檢查沒有發行檔的 Draft、含 manifest／test report 的 Release Candidate，並檢查目前 Package 的實際狀態。它會拒絕只存在其中一份發行證據、manifest 與定義檔 digest 漂移，或 test report 格式無效；若未來有正式 Release Record，還會依 `validator/release.py` 核對它綁定的 manifest 與 report digest。因此執行者建立候選版檔案後，必須在該狀態下重跑同一套測試。

Draft 階段只做開發測試，不執行真實 Study Lifecycle 或正式 Historical Evaluation。v005 專用的 Study 操作技能如有需要，須另行建立並核對；不能把 v004 技能中的版本與資料契約直接當作 v005 指令。
