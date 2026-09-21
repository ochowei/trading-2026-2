# v004：以明確派工取代 Study 核准

本版以 v003 的 Workflow、Policy 綁定、Study 階段規則與既有技能契約為基礎，建立後繼 Package。研究目的、資料區間、候選資格及 terminal 結果定義沿用原規則；Study 改以明確派工驅動，不需要人工核准文件。

v004 的主要結構調整是「Study 引用 Workflow，不複製 Workflow」：每個 Study 在 `manifests/workflow-reference.yml` 保存固定的 Package 路徑與 digest，執行時由 reference resolver 解析同一份 repository Workflow。Development 與 Historical Evaluation 的永久 runtime 只保存 request、runtime manifest 與 evidence／artifact 引用；Workflow、Source Bundle、runner 及資料只進入隔離的暫存執行空間。

交付狀態由 `release-manifest.yml` 與 `release-test-report.yml` 記錄。沒有 `release.yml`，就不是 Active；不得用於正式 Study。本版不修改或遷移 v003。

主要路徑為 created → preregistration-recorded → development-started → Trial／registry／provenance → candidate-frozen → historical-evaluation-started → completed → terminal。歷史評估啟動前先在鎖內保存唯一 operation；started 事件與 authority checkpoint 完成後才讀資料。啟動記號已保存但輸出不完整時，保守判為 indeterminate，不重新執行。

- [操作、計畫與恢復契約](reference/operations.md)
- [研究規格與資料要求](reference/minimal-executable-study.md)
- [驗收與測試對照](IMPLEMENTATION-PLAN.md)
- [v004 Workflow reference contract](reference/workflow-reference.md)
- [建立 Study 至 candidate freeze](../../.agent/skills/build-strategy-study-v004/SKILL.md)
- [blind review](../../.agent/skills/blind-review-strategy-study-v004/SKILL.md)
- [Historical Evaluation 至 terminal](../../.agent/skills/run-strategy-historical-evaluation-v004/SKILL.md)
- [Development 成果卡](../../.agent/skills/study-development-note-authoring-v004/SKILL.md)

所有必要測試使用暫存目錄及合成資料：

```sh
python -m pytest workflows/strategy-forward-replication-research--v004/tests -q
ruff check workflows/strategy-forward-replication-research--v004
```

派工紀錄與 `--role` 是可追查的執行脈絡，不是使用者身分驗證。Workflow Release 仍須由核准者審查後另行建立，實作者不得自行發布。
