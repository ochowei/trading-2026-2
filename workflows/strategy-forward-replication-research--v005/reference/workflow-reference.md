# Workflow reference 契約

v005 的 Study 不再把 Workflow package 複製到自己的 operation runtime。Study 建立時會保存一份 `manifests/workflow-reference.yml`，它是不可變的查找契約，不是 Workflow 的第二份副本。

reference 至少固定以下內容：

- `workflow_package_path`：repository 內 `workflows/strategy-forward-replication-research--v005` 的相對路徑。
- `workflow_digest`：Workflow 定義與規則檔的固定 digest。
- `release_manifest_path` 與 `release_manifest_digest`：同一個 Package 的內容清單；Draft 測試可用 deterministic fallback，正式 Workflow 必須有實體 manifest。
- `policy_set_digest`：被 Workflow 綁定的 Policy release 集合 digest。
- `resolver_version`：目前為 `1`，讓未來改解析規則時可以明確分版。

解析順序是先驗證 reference 的格式與路徑，再確認 Package、Workflow、release manifest、正式 release record（正式模式）及 Policy digest。任何 symlink escape、路徑穿越、受限目錄、版本不一致或 digest 漂移，都在讀取 Study Source Bundle 或資料前拒絕。

Development 與 Historical Evaluation 將 Workflow 與 Source Bundle 複製到各自的隔離暫存 repository，runner 只從該暫存 repository 執行。永久保存的 `runtime/runtime-manifest.yml` 以 path／digest 記錄這次解析與執行，不保存複製出來的 package；這讓多個 Study 可以共用同一份已固定的 Workflow，又保留每次執行可重建、可追查的證據。
