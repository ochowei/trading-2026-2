---
status: accepted
---

# 建議單種類獨立於 Broker Policy

不移植 `firstrade-manual-trading`，改建立 `paper-proposal-orders--v001`：只允許 `MARKET`、`LIMIT` 與觸價後轉市價的 `STOP_MARKET`，拒絕 trailing stop、stop-limit、trailing stop-limit 與所有未列種類。所有輸出都是 non-actionable Proposal，不具 broker 或 live authority；Evaluation、challenges 與 replay 共用相同規則，出現未允許種類時該階段 `fail`。
