# 策略前瞻複製研究 v002

本版改善 Study 建立前的檢查與日常操作入口。研究目的、固定資料區間、事件種類、結果權限、trial 完整性、provenance（資料與既有結果接觸歷史）及候選凍結規則延續前版。建立前會實際執行完整 runner 與正式 Trial 消費路徑；日常流程為 prepare → create-authorize → development → freeze，提供角色分離的 skills 與可恢復 CLI。

此 Package 的交付終點是 Release Candidate。只有 manifest 與測試報告不代表已啟用；沒有 Trusted Approver 建立的 `release.yml`，正式 writer 仍拒絕寫入。v001 與既有 Study 原地保留。

日常使用 [操作指南](reference/operations.md)。研究語意見 [完整指南](reference/strategy-forward-replication-research-v002-guide.md)；測試範圍與已知限制見 [驗收紀錄](IMPLEMENTATION-PLAN.md)。

## 操作差異

| 時點 | 前版操作 | v002 操作 |
| --- | --- | --- |
| 建立前 | precreate／identity／contract／synthetic 等分散檢查；runner 的完整啟動與輸出未涵蓋 | 一次 `prepare`，合併規格、策略合成檢查、完整 Development 與 Historical runner 合成執行及證據重算 |
| 建立與授權 | 人工串接 create、preregistration-approved、development-authorized | 一次 `create-authorize`；逐一寫入相同三事件，必須提供各自核准依據 |
| Development | 人工拆 evidence、發布 artifact、組 Trial | 一次 `development` 保存 candidate／baseline、重算並登錄；執行完成與資格分開 |
| 凍結前 | 人工串 registry、provenance、selection、freeze | 一次 `freeze` 先模擬完整 readiness，再逐事件發布；不合格不能凍結 |
| 中斷 | 依 journal 完成原 bytes | `resume` 接續原 operation／journal；OS 持鎖在程序死亡後釋放，不重複事件或重跑已執行 runner |

## 開發驗證

在 repository 根目錄，以同一已安裝依賴的 Python 環境執行：

```bash
python -m pytest -q workflows/strategy-forward-replication-research--v002/tests
ruff check workflows/strategy-forward-replication-research--v002
```

測試只建立隔離 fixtures，不使用真實 Study 或正式評估資料。測試中的核准與 release 記錄只存在於暫存 fixture，不具有發布權限。
