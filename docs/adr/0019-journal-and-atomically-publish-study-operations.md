---
status: accepted
---

# Study Operations 以 Journal 準備並原子發布

每個 Study 使用單一 lock；guarded writer 先在暫存目錄產生 canonical YAML 與 digests，再以 operation journal 固定準備發布的 exact bytes，依序 atomic rename evidence、event 與 authority checkpoint。中斷後只能完成相同 journal；既有目的檔 bytes 不同時立即停止並回報完整性問題，避免半完成操作或 recovery 偷換 inputs。
