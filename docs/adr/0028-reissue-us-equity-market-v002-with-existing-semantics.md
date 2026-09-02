---
status: accepted
---

# 沿用 US Equity Market v002 的資料語意

本專案重新發布的 market policy 沿用 Yahoo、日線、auto-adjusted prices、XNYS calendar、收盤後 30 分鐘 decision buffer、未知 publication time 至少延遲一個 session，以及 excess lag 預設 fail 的規則。Conformance tests 驗證 session coverage、timezone、publication lag 與 signal suppression；正式 Evaluation 與 Replay 只能讀 frozen Data Snapshots，不在執行時連線 provider。
