---
status: accepted
---

# Release Tests 覆蓋治理規則與失敗情境

Workflow Release 不以抽象行覆蓋率代替行為證據；每條治理規則都要有成功、邊界與失敗案例。必要 suites 包含 canonical YAML、state transitions、trial integrity、provenance、Workflow Floors、九項 challenges、role snapshots、journal recovery、authority rollback、review 重算與 frozen evidence 保護、四種 Study dispositions、無網路／broker safety、policy conformance，以及 v011 完整移除；全部 tests 與 Ruff 通過才可建立 `release.yml`。
