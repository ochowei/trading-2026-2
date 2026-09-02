---
status: accepted
---

# 實作交付 Release Candidate，不自我啟用 Workflow

本次實作完成 workflow rules、validator、guarded writer、tests、examples、docs、`release-manifest.yml` 與測試報告，但不自動建立 `release.yml`。只有獨立的 trusted approver 在檢視 release evidence 後另行明確核准，才能建立 Workflow Release，避免實作者自我啟用權威規則。
