---
status: superseded by ADR-0037
---

# Independent Review 同時要求人員分離與機器重算

Independent Reviewer 不能是 research owner、replay operator 或主要 evidence producer，只能讀 frozen artifacts，不能修補先前 evidence。Deterministic validator 先重算並發布 Terminal Evidence，reviewer 確認後簽署，且只有此流程可以追加最終 outcome event，避免自我核准或信任 caller-reported pass。
