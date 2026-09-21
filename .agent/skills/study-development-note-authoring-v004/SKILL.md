---
name: study-development-note-authoring-v004
description: 為 strategy-forward-replication-research--v004 的單一 Study 撰寫 300–600 字 Development 成果卡；只使用 Development 證據，不讀正式結果。
---

# v004 Development 成果卡

目前角色必須是 **超級管理者** 或 **study 開發者**，且只能處理使用者指定的一個 v004 Study。成果卡是補充說明，不是 evidence、event、authority checkpoint、blind review 或正式 Historical Evaluation。

先讀 `AGENTS.md`，確認本次對話沒有接觸目標 Study 的正式 Evaluation／Terminal outcome；若曝光或讀取範圍不明，停止，不從缺少輸出推定沒有執行。先解析並驗證 `manifests/workflow-reference.yml`，只依 v004 reference 與 digest 取得必要內容。

可讀範圍限於 preregistration、candidate family、prepare settings、Source Bundle 綁定的 Development 規格與程式，以及每個 Trial 的 Development candidate／baseline evidence、inputs、publication、Development provenance 與 selection。禁止開啟、搜尋、雜湊、複製或引用 `historical-evaluation-artifacts/`、正式 Evaluation／Terminal、quarantine／full data、`study.yml`、events、journals、operations 或 Git 歷史。

逐 Trial 區分 formal gates、research targets、evidence validity 與 candidate freeze 資格；target-only fail 不改稱 formal fail，無交易可記錄為合法結果但不可捏造統計值。正文約 300–600 字，使用繁體中文，最多整理三個發現、兩個限制與一個主要下一輪可否證變更；清楚標示已確認、可能原因與尚不能判斷。

預設在對話輸出。只有使用者明確要求寫檔且指定不存在的新路徑時才建立檔案；不得覆寫既有成果卡或修改 Workflow、Study、manifest、evidence、event、authority 或正式結果。結尾列出實際使用的 Development-only 來源與讀取限制，不宣稱已知正式結果。
