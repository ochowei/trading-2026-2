---
status: accepted
---

# Trial 由完整的結果相關 Inputs 識別

策略定義、參數、資料 snapshot、成本、成交與持有規則等 exact digests 共同構成 Trial identity。完全相同 inputs 的技術 retry 不新增名額；任何會影響結果的 input 改變都建立新 Trial 並占用 budget，已查看結果的失敗、移除與放棄版本仍永久保留，避免以重試名義隱藏調參或 selection history。
