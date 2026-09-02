---
status: accepted
---

# Evaluation Folds 各自重設並在年度內暖機

每個年度 Evaluation Fold 都重設 position、cash、cooldown 與 ledger，指標只使用該年度開頭預先固定的 Fold Warmup，且 warmup 不產生 signal、trade 或 performance。策略另需固定最大持有期並在年末套用 entry cutoff，不承接前一年或 2019 quarantine 資料；這會減少可評估 sessions，但能保持年度邊界可重算且不受跨年狀態影響。
