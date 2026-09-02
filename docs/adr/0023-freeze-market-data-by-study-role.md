---
status: accepted
---

# 依 Study Role 分開凍結 Market Data

Development、quarantine、Historical Evaluation 與 2025 Replay 各有獨立 Data Snapshot，保存 provider、symbol、timezone、market calendar、欄位、調整方式、Session Inventory 與 digest。Development 只能取得自己的 snapshot；Evaluation 與 Replay snapshots 在 candidate freeze 前不交給研究者，正式執行不得 refresh 或補資料。Frozen snapshot 可讀但 coverage 不完整時是 `fail`；artifact 無法取得或驗證時是 `indeterminate`。
