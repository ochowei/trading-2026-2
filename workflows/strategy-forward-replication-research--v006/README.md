# v006：讓長期均線條件接受完整的原生檢查

平坦價格加短期下跌，能觸發一般均值回歸，卻通常無法同時滿足 SMA20>SMA50。SMA（簡單移動平均）是最近一段時間收盤價的平均值；本版補上「長期上升、短期回檔後反轉」的人造價格案例，並核對完整指標暖機，避免把案例不足誤當成策略失敗，也避免讓暖機不足或錯誤實作通過。

發布狀態由有效 artifacts（可驗證的發布檔案）判定：尚無有效 Workflow Release 的開發內容是 Draft；完整驗證通過並有 `release-manifest.yml` 與 `release-test-report.yml`，才是 Release Candidate；Trusted Approver 核准且 `release.yml` 與當下 manifest、report、Workflow digest 完全一致，才是 Active。只有 Active 可以建立正式 Study。治理狀態與啟用條件見 [Workflow Lifecycle](../../docs/workflow-lifecycle.md)，不要以本頁文字代替發布證據。

v006 是自包含 Package，沿用 v005 的研究期間、gates（必要資格門檻）、成本、風控、候選凍結、一次歷史評估及 1–16 資產能力，也維持既有單一 CSV 相容性。四份 Policy 與四份 Policy Release 的原始內容保留；Study 引用固定 Workflow 路徑與內容指紋，永久 runtime 保存引用，實際執行空間仍使用隔離暫存目錄。

新的 `indicator_contract.regime` 明列長短視窗、實際指標欄位、使用當日收盤、嚴格大於及未就緒拒絕。原生 guard 從 Close 重算均線與訊號，覆蓋成立、不成立、相等、未就緒、剛就緒、time exit、冷卻差一步與恰好完成。完整 prepare 報告須保存同一來源與契約綁定的原生結果；自行宣稱成功的報告不能取代重新核對的 guard。

- [根因、實際均線與 Control 對照](reference/sma-regime-root-cause.md)
- [可重現 CLI、Schema、拒絕診斷與相容性](reference/synthetic-diagnostics.md)
- [研究操作與角色契約](reference/operations.md)
- [固定 Workflow 引用](reference/workflow-reference.md)
- [1–16 資產與單一 CSV 契約](reference/multi-asset-input.md)
- [開發驗證與完整發布交接](IMPLEMENTATION-PLAN.md)

只需原生合成與靜態驗證時，使用以下範圍限定命令；它們不執行 Study Lifecycle，也不形成 Release Candidate：

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  workflows/strategy-forward-replication-research--v006/tests/test_synthetic_regime.py \
  workflows/strategy-forward-replication-research--v006/tests/test_synthetic_binding.py \
  workflows/strategy-forward-replication-research--v006/tests/test_draft_contracts.py -q
.venv/bin/ruff check workflows/strategy-forward-replication-research--v006
```

完整發布驗證另須執行全部必要 tests、合成 Study 端到端、失敗／恢復與 terminal 案例，再依 Lifecycle 形成 manifest 與 report；這些工作由明確派工的 Workflow 執行者處理。實作者不得自行建立正式 Release。
