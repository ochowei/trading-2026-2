---
status: accepted
---

# 每個 Workflow 都是自包含套件

每個 Workflow Version 自己擁有 workflow definition、schemas、rules、policy bindings、validator、guarded writer、tests、examples 與 reference docs；目前的 Study Events、state machine 與 outcomes 只屬於 `strategy-forward-replication-research--v001`。頂層最多提供 SHA-256、canonical YAML 與 atomic file operations 等無 workflow 語意的可選工具，不建立共同父類別，也不要求未來 workflows 使用相同 stages、events 或 outcomes。
