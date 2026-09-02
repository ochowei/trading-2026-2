---
status: accepted
---

# 分層執行結構、語意與 Artifact 驗證

JSON Schema 負責 YAML 解析後的欄位、型別與 enum，Python semantic validator 負責階段順序、角色分離、trial budget、candidate membership、門檻與 challenge 完整性，artifact verifier 負責安全路徑、SHA-256 與 digest bindings。Guarded writer 與 independent review 共用同一驗證核心，並新增 `jsonschema` dependency，避免兩套規則逐漸分歧。
