---
status: accepted
---

# 區分 Fail、Indeterminate 與 Paused

可可靠計算但未達必要門檻時是 `fail`；身份、digest、provenance 或 evidence 不足而無法可信判定時是 `indeterminate`；只有 frozen inputs 完整且問題可用相同 inputs 恢復時才是 `paused`。`fail` 與 `indeterminate` 都會終止原 Study，`paused` 不產生 outcome，避免把技術中斷誤報為策略失敗，或用 recovery 偷換策略與門檻。
