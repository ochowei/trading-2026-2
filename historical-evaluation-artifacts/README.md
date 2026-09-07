# Historical Evaluation 結果資料夾

本資料夾專門保存 Historical Evaluation 結果，並納入 Git 版本追蹤。

使用規則：

- 只有「超級管理者」與「Study 歷史評估執行者」可以讀取或寫入。
- 其他角色不得開啟、搜尋、引用其中內容，也不得根據其中內容做決策。
- 既有 artifact 不得覆寫或刪除；新結果只能以新檔案或新版本新增。
- 這些是 AI Agent 的流程規範，不是 Git 或作業系統的實際權限控制。

正式 Writer／Validator 已整合本資料夾。新的 Historical Evaluation 結果使用下列 repository-relative path：

```text
historical-evaluation-artifacts/
└── <study-id>/
    ├── historical-evaluation.yml
    ├── historical-evaluation-report.yml   # 若該次操作產生詳細報告
    └── terminal-evidence.yml
```

使用 guarded writer 發布時，`artifact_path` 會記錄完整的
`historical-evaluation-artifacts/<study-id>/...` 路徑；Validator 會從同一個 store 讀取、
檢查 canonical YAML 與 SHA-256 digest，再重新計算 Historical Evaluation gates。

其他研究階段的 manifests、Development evidence 與 provenance 仍放在
`workflows/.../studies/<study-id>/` 內。既有 Study 已發布在舊 `studies/<study-id>/evidence/`
下的結果不搬移、不覆寫，Validator 會繼續支援它們；新的正式 Historical Evaluation 與
Terminal Evidence 才使用本資料夾。
