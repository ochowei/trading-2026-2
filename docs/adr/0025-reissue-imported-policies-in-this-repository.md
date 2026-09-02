---
status: accepted
---

# 移植 Policy 內容並在本專案重新發布

從 `trading-2026-1` 的 active policies 移植實際規則值，但不沿用原 `RELEASE.json` 或 release identity，因為它們綁定本專案不存在的 implementations 與 tests。新專案使用 canonical YAML 重新建立 Policy Releases，綁定本專案的實作與 conformance tests，重新計算 digests 並記錄來源，避免把無法驗證的舊 release 冒充為有效本地規則。
