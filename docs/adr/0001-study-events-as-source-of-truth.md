---
status: accepted
---

# 以研究事件作為 Study 狀態的唯一事實來源

Study 的階段與結果以不可改寫、只能依序新增的 Study Events 為唯一事實來源，`study.yml` 只保存由事件推導出的目前狀態摘要，不接受直接修改。這比直接更新 manifest 複雜，但能讓 Study 正常推進，同時避免改寫歷史或跳過階段直接宣告通過。
