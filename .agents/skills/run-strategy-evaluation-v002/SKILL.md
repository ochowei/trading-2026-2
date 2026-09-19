---
name: run-strategy-evaluation-v002
description: 僅在 Study 歷史評估執行者角色及使用者明確要求下，透過 v002 CLI 對已凍結 Study 執行一次 Historical Evaluation 並完成 Terminal。不建立或調整策略，不適用 v001。
---

目前角色必須是 Study 歷史評估執行者，不自行切換角色。僅在使用者明確要求對指定 `strategy-forward-replication-research--v002` Study 執行或接續 Historical Evaluation 時使用；收到開發 skill 交接本身不是授權。

讀取 AGENTS.md 與 `workflows/strategy-forward-replication-research--v002/reference/operations.md` 的 Evaluation 契約。確認本版已核准啟用；正式研究不得使用 `--allow-draft`。不改 candidate、preregistration、source、門檻或已完成 evidence。

先呼叫固定版本 CLI：

```text
python workflows/strategy-forward-replication-research--v002/operations/cli.py --repository-root <repo> --authority-root <bound-root> --role 'Study 歷史評估執行者' status <id>
```

從事件狀態與 frozen candidate 判斷下一步，不假設第 7 或第 8 個事件是固定階段。缺少 freeze 或本次評估核准時，只整理具體缺件。核准必須綁定 Study、preregistration、source 及 candidate freeze 指紋；不替核准者產生核准。

取得明確執行要求、既有核准及 frozen dataset 後使用：

```text
python workflows/strategy-forward-replication-research--v002/operations/cli.py --repository-root <repo> --authority-root <bound-root> --role 'Study 歷史評估執行者' historical-evaluation <id> --plan <evaluation.yml>
```

CLI 使用受測 runner、離線隔離資料、重算結果、保存不可覆寫證據並完成 Terminal。正式結果與 runtime 輸出只位於 `historical-evaluation-artifacts/<id>/`；不要把評估結果複製到開發文件或其他目錄。不得連網下載資料或下單。

程序中斷後以相同角色呼叫 `resume <id>`。若已有 started 記錄但沒有完整輸出，CLI 會停止自動重跑；先判定 exposure、保留原操作紀錄，再依既有不可恢復程序處理。不能以「沒有產出 evidence」宣稱沒有見過結果。

成功完成只回報 Study 狀態、驗證結果與專用 store 的 artifact 路徑；不把 gate fail 當成程式故障重跑，不自行開啟下一輪研究。工作進度留給專案管理者驗收，不移到 Done。
