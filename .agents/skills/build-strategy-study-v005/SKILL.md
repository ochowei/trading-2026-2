---
name: build-strategy-study-v005
description: 為 strategy-forward-replication-research--v005 建立或接續單一 Study，完成 Development 到 candidate freeze；限 study 開發者，不執行 Historical Evaluation。
---

# v005 Study Development

目前角色必須是 **study 開發者**。本 skill 只處理一個明確指定的 Study 與 `development-to-freeze` 派工；不得自行改扮 Study 歷史評估執行者、workflow 維護者或超級管理者。先依 `AGENTS.md` 確認角色與資料權限。

## 派工與固定入口

v005 不要求額外人工核准或簽章。把已收到的明確指令整理成 canonical YAML 派工，依 `schemas/assignment.schema.yml` 記錄真實的 `source_id`、指令原文或可追查摘錄、指派者、受派者、角色、Study ID、`workflow_version: v005` 與 `scope: development-to-freeze`。不得用範例派工當成真實指派，也不得捏造缺少的事實；若實際 Study、任務範圍、研究決策或 provenance 仍不明確，先停止並補齊所需資訊。模糊的「繼續研究」或開發交接不構成正式評估派工。

開始前讀取 Workflow 的 `reference/operations.md`、`reference/workflow-reference.md` 與 `reference/minimal-executable-study.md`；多資產輸入時另讀 `reference/multi-asset-input.md`。正式 Study 必須使用有效的 Active `release.yml`，並確認 release manifest、Workflow digest 與 Policy set digest 相符。Draft 或 Release Candidate 不可建立正式 Study；`--allow-draft` 只供隔離 fixture。

正式操作固定使用 v005 CLI；全域參數放在子命令前，沿用 Study 綁定的原 authority root：

```sh
python3 workflows/strategy-forward-replication-research--v005/operations/cli.py \
  --repository-root <repo> --authority-root <原authority> --role 'study 開發者' \
  develop-to-freeze <Study-ID> --plan <連續計畫.yml> --assignment <派工.yml>
```

連續計畫必須包含 `create`、`development` 陣列與 `freeze`。`develop-to-freeze` 會依序執行 prepare、create、各 Trial、registry、provenance、readiness 與 freeze；prepare 會驗證固定研究輸入並執行隔離的合成 runner。若採分段命令，依 v005 操作契約使用 `prepare`、`create`、`development`、`freeze-readiness`、`freeze` 或符合條件的 `terminate`，每個寫入步驟都帶同一份派工。不要使用 v004 CLI、舊核准欄位或低階 writer 來繞過派工檢查。

## Workflow reference 與執行隔離

在讀取 Study 的 Source Bundle、資料或 runner 前，先解析並驗證 `manifests/workflow-reference.yml`。確認它固定指向 repository 內的 v005 Package，並逐一核對 reference digest、Workflow digest、release manifest digest、正式 release record 與 Policy set digest。路徑穿越、symlink escape、受限路徑、版本不符或 digest 漂移都要停止處理；不要以 Study 內的副本替代 reference。

Workflow、Source Bundle、runner、資料及 runner output 只放在該次 operation 的隔離暫存 workspace。Study 永久 runtime 僅保存 `runtime/request.yml`、`runtime/runtime-manifest.yml` 及必要的 evidence／artifact 引用；manifest 要記錄各輸入與輸出的 digest，並標示 `execution_workspace: temporary`。Source Bundle 是此 Study 自己綁定的來源，不是共用 Workflow；不要把暫存資料檔或 Workflow Package 留在永久 runtime。

## Development 資料

新式 `data_assets` 支援 1–16 個資產，須按唯一 `asset_id` 排序，恰有一個 `use: trade`，其餘為 `reference`。每筆各自記錄 provider、symbol、repository-relative `data_path`、該檔 SHA-256 `data_digest`、日期範圍、`timezone: America/New_York`、`available_at: after-close` 與 `interval_role: warmup-development`。每份 CSV 都要獨立驗 digest；清單必須和 `trial_inputs.data_bindings.assets` 完全相同。不得同時使用 `data_assets` 與舊式單資產 `data_path`／`data_digest` 欄位。

舊式單資產 Study 可繼續使用一組 `data_path`／`data_digest`。資料路徑必須留在 repository 內且不進受限目錄；runner 收到的多資產檔案只映射到隔離暫存空間的 `run/assets/<asset_id>.csv`，不得把原始 CSV 永久保存進 operation runtime。

每檔 CSV 必須是 `Date,Open,High,Low,Close,Volume` 六欄，使用 XNYS 交易日，日期完整遞增且不重複；多資產的交易日清單要完全一致。不得前填、插值或自動取交集。固定限制為每檔最多 32 MiB／10,000 列、總量最多 128 MiB。Development 僅能讀取預先固定的 warmup 與 development 範圍，不得讀取 quarantine 或 Historical Evaluation 價格／結果。收盤價在收盤後才可得，當日訊號最早只能用於下一個交易日；不能只憑 request 欄位推定 runner 沒有前視偏差。

## 合法範圍、停止與交接

依 preregistration 開發並記錄所有可能影響選擇的版本；失敗、放棄或移除的 outcome-relevant 變體也要列入 append-only trial registry。每個 Trial 都必須有符合 schema 的 candidate 與 baseline 輸出，並以 digest 綁定計畫、資料、Source Bundle 與 publication。freeze 前完成 provenance audit、固定完整 trial family，並依預先登記的資格與選擇次序挑選至多一個候選。不得把缺 baseline、缺 provenance、選擇次序錯誤或門檻漂移改寫成通過。合法的績效 fail 仍是研究證據；只有 lifecycle 容許的失敗或證據不足事實才能用 `terminate`，不得自行製造通過結果。

完成 candidate freeze 或形成合法的 Development terminal 後立即停止。不得執行 `historical-evaluation`、讀取／寫入 `historical-evaluation-artifacts/`、查看正式 Evaluation 結果、修改已 frozen 的候選／門檻，或宣稱正式評估結論。Freeze 所需的 snapshot metadata 與 session inventory 可供核對，但不可藉此讀取 Evaluation 價格或結果。

遇到可恢復的中斷時，以原 Study、原派工、原連續計畫、原 authority 與同一 operation 恢復；`resume` 必須帶回原派工。不要建立第二個 operation，也不要重跑已完成的 runner。若 release/reference、digest、資料資格或角色權限失敗，先停止並回報實際缺件／錯誤，不要用 Draft 模式或手動發布 Event、runtime manifest 或 evidence 繞過驗證。開發角色的 `status`／`validate` 只檢查 Development prefix，不代表後續階段已驗證。

交接時提供 Study ID、v005 派工範圍與派工 digest、原 authority root、Workflow reference path／digest、Source Bundle digest、operation ID、目前 event head、candidate freeze 或 terminal 狀態，以及未完成步驟與缺件。交接後由有權角色依其自身派工處理後續工作。
