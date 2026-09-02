---
status: accepted
---

# 所有正式檔案使用 Repository-Canonical YAML

Workflow、preregistration、Study Events 與正式 evidence 統一使用 YAML；由 guarded writer 依 repository-defined canonical profile 輸出 UTF-8、LF、兩格縮排、固定 key 排序、字串日期與小數、無 anchors、aliases、自訂 tags 或註解，並保留單一檔尾換行。Digest 以輸出的 exact bytes 計算，validator 重新序列化後必須得到完全相同 bytes，兼顧閱讀性與穩定 identity。
