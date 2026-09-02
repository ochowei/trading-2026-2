---
status: accepted
---

# Independent Review 指獨立重算，不要求人員分離

Independent Reviewer 可以和 research owner、replay operator 或 evidence producer 是同一人；本 workflow 信任檔案填寫者，不以角色分離提供安全保證。Review 的必要獨立性來自使用 frozen inputs 與 raw evidence 重新計算、拒絕 caller-reported pass，且 review 過程不能修改既有 evidence；只有完成這個重算流程才能追加最終 outcome event。
