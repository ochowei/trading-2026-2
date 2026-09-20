---
name: run-strategy-evaluation-v003
description: 由 Study 歷史評估執行者依既有明確派工對凍結 v003 Study 執行唯一歷史評估至 terminal。
---

目前角色須為 Study 歷史評估執行者，不自行切換。先讀取 AGENTS.md 與本 Package 的 reference/operations.md。正式 Study 必須已存在有效 Workflow Release，不能使用 --allow-draft。

僅處理明確指定 Study 與 historical-evaluation-to-terminal 的派工。可保存已收到指令的來源、原文或可追查摘錄，不另要求核准文件、簽名或最終 candidate digest 的再次確認。開發交接或模糊的繼續研究不是評估派工；缺少實際範圍時才詢問。

使用版本固定 CLI，明示 --role 'Study 歷史評估執行者'，執行 historical-evaluation STUDY --plan PATH --assignment PATH。計畫保留 actor、data_path、data_digest；候選、資料、runner 與派工由工具綁定，不加入 authorization。

只以原派工、plan、source 與 authority 恢復同一 operation。工具先 reservation、started 與 checkpoint，後讀資料，啟動前另寫不可覆寫 marker。已有 marker 而輸出不完整時不得重跑，接受 evidence-unavailable／indeterminate；不得刪除輸出或更換 operation 取得第二次評估。

不調整策略、門檻或 candidate。結果與 runtime 只寫專用 artifact store，完成 terminal 後交付事件與證據引用，不自行標記專案看板 Done。
