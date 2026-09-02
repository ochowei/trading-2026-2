---
status: superseded by ADR-0015
---

# Git 保存 Study Authority，但不保存大型或敏感 Artifacts

Study Events、preregistration、candidate freeze、gate results、metrics、digest manifests 與 Terminal Evidence 進 Git；大型 market-data snapshots、逐筆 ledger 與敏感原始檔放在不可覆寫的 content-addressed storage，由 Git 內的 Evidence Manifest 保存位置、大小、SHA-256 與 session inventory。Reviewer 無法取得或驗證 exact artifact 時結果為 `indeterminate`，而 `workflows/` 只保存規則。
