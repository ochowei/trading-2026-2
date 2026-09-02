---
status: accepted
---

# 沿用 Canonical Execution v001 的成交語意

本專案重新發布的 canonical execution policy 沿用來源規則：next-session open market entry、day limit target、GTC stop-market、next-session open expiry，日內同時觸及 target 與 stop 時採 adverse stop first，缺少下一 session 時 unfilled。Base costs 為進出各 5 bps slippage 加每邊 1 bps fee；stress costs 為進出各 20 bps slippage 加每邊 2 bps fee。
