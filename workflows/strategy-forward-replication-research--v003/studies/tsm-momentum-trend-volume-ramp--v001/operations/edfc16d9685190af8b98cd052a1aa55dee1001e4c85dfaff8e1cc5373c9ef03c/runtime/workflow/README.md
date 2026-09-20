# v003：以明確派工取代 Study 核准

本版以 v002 為基礎，依 `docs/plans/study-explicit-assignment-lifecycle.md` 建立後繼 Package。研究目的、資料區間、Policy、候選資格及 terminal 結果定義沿用原規則；Study 改以既有明確派工驅動，不需要人工核准文件。

交付狀態由 `release-manifest.yml` 與 `release-test-report.yml` 記錄。沒有 `release.yml`，就不是 Active；不得用於正式 Study。本版不修改或遷移 v002。

主要路徑為 created → preregistration-recorded → development-started → Trial／registry／provenance → candidate-frozen → historical-evaluation-started → completed → terminal。歷史評估啟動前先在鎖內保存唯一 operation；started 事件與 authority checkpoint 完成後才讀資料。啟動記號已保存但輸出不完整時，保守判為 indeterminate，不重新執行。

- [操作、計畫與恢復契約](reference/operations.md)
- [研究規格與資料要求](reference/minimal-executable-study.md)
- [驗收與測試對照](IMPLEMENTATION-PLAN.md)
- [Development skill](skills/build-strategy-study-v003/SKILL.md)
- [評估 skill](skills/run-strategy-evaluation-v003/SKILL.md)

所有必要測試使用暫存目錄及合成資料：

```sh
python -m pytest workflows/strategy-forward-replication-research--v003/tests -q
ruff check workflows/strategy-forward-replication-research--v003
```

派工紀錄與 `--role` 是可追查的執行脈絡，不是使用者身分驗證。Workflow Release 仍須由核准者審查後另行建立，實作者不得自行發布。
