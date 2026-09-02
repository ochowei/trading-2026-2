---
status: accepted
---

# 使用簡化的本機 Append-Only Authority Store

每次 Study Event 發布後，在設定的本機 authority root 以 atomic create 新增 head checkpoint YAML，不使用資料庫、Git 或外部服務；checkpoint 不得覆寫，且 authority root 不位於單一 Study 目錄內。Validator 比對 event chain 與最新 checkpoint，以偵測意外回退或部分遺失，但不宣稱能阻止有檔案權限的人故意刪除兩邊資料。
