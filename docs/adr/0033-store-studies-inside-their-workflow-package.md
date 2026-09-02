---
status: accepted
---

# Studies 位於所屬 Workflow Package 內

每個 Study 放在 `workflows/<workflow-id>--<version>/studies/<study-id>/`，使不同 workflows 能擁有不同 runtime layout。Workflow digest 只計算 `release-manifest.yml` 明確列出的 definition、schema、rules、policies 與 maintained implementation files，永遠排除 `studies/`；大型或敏感 artifacts 仍存放於外部 content-addressed storage。
