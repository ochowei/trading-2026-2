---
status: accepted
---

# Guarded writer 是 Study 的唯一正式寫入路徑

所有正式 Study 變更都必須由 guarded writer 驗證前置條件後追加 Study Event；validator 仍提供獨立重算，但不把事後檢查當成主要防線。直接修改事件、推導狀態或 outcome 會造成完整性失敗，因為無法證明修改遵循流程順序與不可改寫規則。
