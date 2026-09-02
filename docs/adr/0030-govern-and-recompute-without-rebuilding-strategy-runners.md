---
status: accepted
---

# 治理並重算 Evidence，不重建完整策略 Runner

本次實作接受外部 runner 產生的 canonical signals、trades、fills 與 ledger evidence，綁定其 Source Bundle，並從 raw evidence 重算 metrics 與 gates，不信任 caller-reported pass。專案提供 execution-policy conformance tests 與 fixture runner 的端到端範例，但不在本次重建任意策略 signal engine 或九項 challenge generators，避免 workflow 修復擴張成完整交易平台重寫。
