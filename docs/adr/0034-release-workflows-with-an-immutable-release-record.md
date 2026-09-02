---
status: accepted
---

# 以不可改寫的 Release Record 啟用 Workflow

開發中的 Workflow Package 沒有 `release.yml`，一律視為 draft；`release-manifest.yml` 列出全部權威檔案與 digests，通過 schema、validator、policy conformance、正反例和端到端測試後，由 trusted approver 一次性建立 `release.yml`。Guarded writer 只接受有效 release；啟用後權威檔案不得修改，任何規則修正建立下一個 Workflow Version。
