# 策略前瞻複製研究 v002

本版改善 Study 建立前的檢查與日常操作入口。研究目的、固定資料區間、事件種類、結果權限、trial 完整性、provenance（資料與既有結果接觸歷史）及候選凍結規則延續前版。新增的是在第一個事件前實際執行完整 runner 的檢查，以及可接續的三事件建立操作。

此 Package 的交付終點是 Release Candidate。只有 manifest 與測試報告不代表已啟用；沒有 Trusted Approver 建立的 `release.yml`，正式 writer 仍拒絕寫入。v001 與既有 Study 原地保留。

日常使用 [操作指南](reference/operations.md)。研究語意見 [完整指南](reference/strategy-forward-replication-research-v002-guide.md)；測試範圍與已知限制見 [驗收紀錄](IMPLEMENTATION-PLAN.md)。

## 操作差異

| 時點 | 前版操作 | v002 操作 |
| --- | --- | --- |
| 建立前 | precreate／identity／contract／synthetic 等分散檢查；runner 的完整啟動與輸出未涵蓋 | 一次 `prepare`，合併規格、策略合成檢查、完整 Development 與 Historical runner 合成執行及證據重算 |
| 建立與授權 | 人工串接 create、preregistration-approved、development-authorized | 一次 `create-authorize`；逐一寫入相同三事件，必須提供各自核准依據 |
| 凍結前 | `all` 名稱容易被誤認為完整流程已檢查 | `freeze-readiness` 模擬真正 candidate-frozen 事件，通過才進行凍結 |
| 中斷 | 依 journal 完成原 bytes | 保留原 journal；相同 plan 與 report 重試，不重複追加已完成事件 |

## 開發驗證

在 repository 根目錄，以同一已安裝依賴的 Python 環境執行：

```bash
python -m pytest -q workflows/strategy-forward-replication-research--v002/tests
ruff check workflows/strategy-forward-replication-research--v002
```

測試只建立隔離 fixtures，不使用真實 Study 或正式評估資料。測試中的核准與 release 記錄只存在於暫存 fixture，不具有發布權限。
