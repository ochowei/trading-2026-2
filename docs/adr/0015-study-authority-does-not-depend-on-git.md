---
status: accepted
---

# Study Authority 不依賴 Git

Study 的建立、寫入、驗證、recovery 與 independent review 都不得要求 Git；Events 使用 digest chain，最新 sequence 與 head digest 另寫入 repository 之外的 append-only authority store，以偵測整段尾端回退。第一版提供 atomic、禁止覆寫的本機 backend，並保留 WORM/object-lock storage 或 transparency log backend 介面；Git 只可作為選用的備份與 review 管道，本機 backend 的威脅模型則明確不宣稱能抵抗擁有最高檔案權限的人刪除全部 authority records。
