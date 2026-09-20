---
name: build-strategy-study-v003
description: 以既有明確派工建立或接續 v003 Development Study 至候選凍結；僅 study 開發者使用。
---

目前角色須為 study 開發者，不自行切換。先讀取 AGENTS.md 與本 Package 的 reference/operations.md。正式 Study 必須已存在有效 Workflow Release，不能使用 --allow-draft。

保存使用者已給定的 Study、角色與 development-to-freeze 派工原文或可追查摘錄，不請使用者另外簽核。缺少實際範圍、研究決策或 provenance 事實時才補問；不得虛構指派者、verified-clean 或未接觸結果。

依固定版本 CLI，以明示 --role 'study 開發者' 執行 prepare、create、development、freeze-readiness、freeze，或使用共用驗證的 develop-to-freeze。所有寫入提供 --assignment，原 plan、source 與 authority 不可因結果更換。中斷時以相同派工 resume。

不讀評估 store、管理者專屬資料夾或後續評估結果，不執行正式歷史評估。candidate-frozen 即完成本階段派工，交接 Study ID、v003、authority、事件 head 與實際缺件。status 的 not_inspected 不能宣稱完整語意驗證。
