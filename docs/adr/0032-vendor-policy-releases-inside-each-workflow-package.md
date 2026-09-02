---
status: accepted
---

# 每個 Workflow Package 內含自己的 Policy Releases

`strategy-forward-replication-research--v001` 將重新發布的 market、execution、portfolio-risk 與 paper-proposal-orders policies 放在自己的 `policies/` 目錄並綁定 exact digests，不解析 repository 頂層的 active 或 latest registry。未來 workflow 自行包含所需 immutable policy copies；接受少量重複，以換取單一 package 可獨立搬移與驗證。
